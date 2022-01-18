//
//! Copyright 2020 Alibaba Group Holding Limited.
//!
//! Licensed under the Apache License, Version 2.0 (the "License");
//! you may not use this file except in compliance with the License.
//! You may obtain a copy of the License at
//!
//! http://www.apache.org/licenses/LICENSE-2.0
//!
//! Unless required by applicable law or agreed to in writing, software
//! distributed under the License is distributed on an "AS IS" BASIS,
//! WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//! See the License for the specific language governing permissions and
//! limitations under the License.

use std::error::Error;
use std::fmt::Debug;
use std::net::SocketAddr;
use std::pin::Pin;
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::Arc;
use std::task::{Context, Poll};
use std::time::Duration;

use futures::Stream;
use hyper::server::accept::Accept;
use hyper::server::conn::{AddrIncoming, AddrStream};
use pegasus::api::function::FnResult;
use pegasus::api::FromStream;
use pegasus::result::{FromStreamExt, ResultSink};
use pegasus::{Configuration, Data, JobConf, ServerConf};
use pegasus_network::ServerDetect;
use prost::Message;
use serde::Deserialize;
use tokio::sync::mpsc::UnboundedSender;
use tokio_stream::wrappers::UnboundedReceiverStream;
use tonic::transport::Server;
use tonic::{Code, Request, Response, Status};

use crate::generated::protocol as pb;
use crate::generated::protocol::job_config::Servers;
use crate::service::{JobDesc, JobParser, Service};

pub struct RpcSink {
    pub job_id: u64,
    had_error: Arc<AtomicBool>,
    peers: Arc<AtomicUsize>,
    tx: UnboundedSender<Result<pb::JobResponse, Status>>,
}

impl RpcSink {
    pub fn new(job_id: u64, tx: UnboundedSender<Result<pb::JobResponse, Status>>) -> Self {
        RpcSink {
            tx,
            had_error: Arc::new(AtomicBool::new(false)),
            peers: Arc::new(AtomicUsize::new(1)),
            job_id,
        }
    }
}

impl<T: Message> FromStream<T> for RpcSink {
    fn on_next(&mut self, next: T) -> FnResult<()> {
        let data = next.encode_to_vec();
        let res = pb::JobResponse { job_id: self.job_id, res: Some(pb::BinaryResource { resource: data }) };
        self.tx.send(Ok(res)).ok();
        Ok(())
    }
}

impl Clone for RpcSink {
    fn clone(&self) -> Self {
        self.peers.fetch_add(1, Ordering::SeqCst);
        RpcSink {
            job_id: self.job_id,
            had_error: self.had_error.clone(),
            peers: self.peers.clone(),
            tx: self.tx.clone(),
        }
    }
}

impl<T: Message> FromStreamExt<T> for RpcSink {
    fn on_error(&mut self, error: Box<dyn Error + Send>) {
        self.had_error.store(true, Ordering::SeqCst);
        let status = Status::unknown(format!("execution_error: {}", error));
        self.tx.send(Err(status)).ok();
    }
}

impl Drop for RpcSink {
    fn drop(&mut self) {
        let before_sub = self.peers.fetch_sub(1, Ordering::SeqCst);
        if before_sub == 1 {
            if !self.had_error.load(Ordering::SeqCst) {
                self.tx.send(Err(Status::ok("ok"))).ok();
            }
        }
    }
}

#[derive(Clone)]
pub struct JobServiceImpl<I: Data, O, P> {
    inner: Service<I, O, P>,
    report: bool,
}

#[tonic::async_trait]
impl<I, O, P> pb::job_service_server::JobService for JobServiceImpl<I, O, P>
where
    I: Data,
    O: Send + Debug + Message + 'static,
    P: JobParser<I, O>,
{
    type SubmitStream = UnboundedReceiverStream<Result<pb::JobResponse, Status>>;

    async fn submit(&self, req: Request<pb::JobRequest>) -> Result<Response<Self::SubmitStream>, Status> {
        debug!("accept new request from {:?};", req.remote_addr());
        let pb::JobRequest { conf, source, plan, resource } = req.into_inner();
        if conf.is_none() {
            return Err(Status::new(Code::InvalidArgument, "job configuration not found"));
        }

        let conf = parse_conf_req(conf.unwrap());
        pegasus::wait_servers_ready(conf.servers());
        let (tx, rx) = tokio::sync::mpsc::unbounded_channel();
        let rpc_sink = RpcSink::new(conf.job_id, tx);
        let sink = ResultSink::<O>::with(rpc_sink);
        if conf.trace_enable {
            info!("submitting job {} with id {}", conf.job_name, conf.job_id);
        }
        let job_id = conf.job_id;
        let service = &self.inner;
        let job = JobDesc {
            input: source.map(|b| b.resource).unwrap_or(vec![]),
            plan: plan.map(|b| b.resource).unwrap_or(vec![]),
            resource: resource.map(|b| b.resource).unwrap_or(vec![]),
        };

        let submitted = pegasus::run_opt(conf, sink, move |worker| worker.dataflow(service.accept(&job)));

        if let Err(e) = submitted {
            error!("submit job {} failure: {:?}", job_id, e);
            return Err(Status::invalid_argument(format!("submit job error {}", e)));
        }

        Ok(Response::new(UnboundedReceiverStream::new(rx)))
    }
}

#[derive(Debug, Deserialize)]
pub struct RPCServerConfig {
    pub rpc_host: Option<String>,
    pub rpc_port: Option<u16>,
    pub rpc_concurrency_limit_per_connection: Option<usize>,
    pub rpc_timeout: Option<Duration>,
    pub rpc_initial_stream_window_size: Option<u32>,
    pub rpc_initial_connection_window_size: Option<u32>,
    pub rpc_max_concurrent_streams: Option<u32>,
    pub rpc_keep_alive_interval: Option<Duration>,
    pub rpc_keep_alive_timeout: Option<Duration>,
    pub tcp_keep_alive: Option<Duration>,
    pub tcp_nodelay: Option<bool>,
}

pub struct RPCJobServer<S: pb::job_service_server::JobService> {
    service: S,
    rpc_config: RPCServerConfig,
    server_config: pegasus::Configuration,
}

pub async fn start_rpc_server<I, O, P, D, E>(
    rpc_config: RPCServerConfig, server_config: Configuration, service: Service<I, O, P>,
    server_detector: D, listener: E,
) -> Result<(), Box<dyn std::error::Error>>
where
    I: Data,
    O: Send + Debug + Message + 'static,
    P: JobParser<I, O>,
    D: ServerDetect + 'static,
    E: ServiceStartListener,
{
    let service = JobServiceImpl { inner: service, report: true };
    let server = RPCJobServer::new(rpc_config, server_config, service);
    server.run(server_detector, listener).await?;
    Ok(())
}

impl<S: pb::job_service_server::JobService> RPCJobServer<S> {
    pub fn new(rpc_config: RPCServerConfig, server_config: Configuration, service: S) -> Self {
        RPCJobServer { service, rpc_config, server_config }
    }

    pub async fn run<D, E>(
        self, server_detector: D, mut listener: E,
    ) -> Result<(), Box<dyn std::error::Error>>
    where
        D: ServerDetect + 'static,
        E: ServiceStartListener,
    {
        let RPCJobServer { service, mut rpc_config, server_config } = self;
        let server_id = server_config.server_id();
        if let Some(server_addr) = pegasus::startup_with(server_config, server_detector)? {
            listener.on_server_start(server_id, server_addr)?;
        }

        let mut builder = Server::builder();
        if let Some(limit) = rpc_config.rpc_concurrency_limit_per_connection {
            builder = builder.concurrency_limit_per_connection(limit);
        }

        if let Some(dur) = rpc_config.rpc_timeout.take() {
            builder.timeout(dur);
        }

        if let Some(size) = rpc_config.rpc_initial_stream_window_size {
            builder = builder.initial_stream_window_size(Some(size));
        }

        if let Some(size) = rpc_config.rpc_initial_connection_window_size {
            builder = builder.initial_connection_window_size(Some(size));
        }

        if let Some(size) = rpc_config.rpc_max_concurrent_streams {
            builder = builder.max_concurrent_streams(Some(size));
        }

        if let Some(dur) = rpc_config.rpc_keep_alive_interval.take() {
            builder = builder.http2_keepalive_interval(Some(dur));
        }

        if let Some(dur) = rpc_config.rpc_keep_alive_timeout.take() {
            builder = builder.http2_keepalive_timeout(Some(dur));
        }

        let service = builder.add_service(pb::job_service_server::JobServiceServer::new(service));

        let host = rpc_config
            .rpc_host
            .clone()
            .unwrap_or("0.0.0.0".to_owned());
        let addr = SocketAddr::new(host.parse()?, rpc_config.rpc_port.unwrap_or(0));
        let incoming =
            TcpIncoming::new(addr, rpc_config.tcp_nodelay.unwrap_or(true), rpc_config.tcp_keep_alive)?;
        info!("starting RPC job server on {} ...", incoming.inner.local_addr());
        listener.on_rpc_start(server_id, incoming.inner.local_addr())?;

        service.serve_with_incoming(incoming).await?;
        Ok(())
    }
}

pub trait ServiceStartListener {
    fn on_rpc_start(&mut self, server_id: u64, addr: SocketAddr) -> std::io::Result<()>;

    fn on_server_start(&mut self, server_id: u64, addr: SocketAddr) -> std::io::Result<()>;
}

pub(crate) struct TcpIncoming {
    inner: AddrIncoming,
}

impl TcpIncoming {
    pub(crate) fn new(addr: SocketAddr, nodelay: bool, keepalive: Option<Duration>) -> hyper::Result<Self> {
        let mut inner = AddrIncoming::bind(&addr)?;
        inner.set_nodelay(nodelay);
        inner.set_keepalive(keepalive);
        Ok(TcpIncoming { inner })
    }
}

impl Stream for TcpIncoming {
    type Item = Result<AddrStream, std::io::Error>;

    fn poll_next(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        Pin::new(&mut self.inner).poll_accept(cx)
    }
}

fn parse_conf_req(mut req: pb::JobConfig) -> JobConf {
    let mut conf = JobConf::new(req.job_name);
    if req.job_id != 0 {
        conf.job_id = req.job_id;
    }

    if req.workers != 0 {
        conf.workers = req.workers;
    }

    if req.time_limit != 0 {
        conf.time_limit = req.time_limit;
    }

    if req.batch_size != 0 {
        conf.batch_size = req.batch_size;
    }

    if req.batch_capacity != 0 {
        conf.batch_capacity = req.batch_capacity;
    }

    if req.trace_enable {
        conf.trace_enable = true;
        conf.plan_print = true;
    }

    if let Some(servers) = req.servers.take() {
        match servers {
            Servers::Local(_) => conf.reset_servers(ServerConf::Local),
            Servers::Part(mut p) => {
                if !p.servers.is_empty() {
                    let vec = std::mem::replace(&mut p.servers, vec![]);
                    conf.reset_servers(ServerConf::Partial(vec))
                }
            }
            Servers::All(_) => conf.reset_servers(ServerConf::All),
        }
    }
    conf
}
