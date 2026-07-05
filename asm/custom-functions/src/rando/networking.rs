use core::{
    borrow::BorrowMut,
    cell::Cell,
    ffi::{c_int, c_uint, c_ushort, c_void, CStr},
    fmt::{Debug, Write},
    future::Future,
    mem::size_of_val,
    net::Ipv4Addr,
    pin::Pin,
    ptr::copy_nonoverlapping,
    ptr::null_mut,
    slice,
    task::{Context, Poll, RawWaker, RawWakerVTable, Waker},
};

use alloc::string::String;
use alloc::string::ToString;
use alloc::{boxed::Box, vec::Vec};
use cstr::cstr;

use crate::{
    game::{
        file_manager,
        flag_managers::{self, SceneflagManager, StoryflagManager},
    },
    println,
    rando::{
        multiworld::{
            self, read_bytes_from_address, write_bytes_to_address, APLocationInfo, APStatusReport,
            ARCHIPELAGO_SLOT_NAME, ARCHIPELAGO_TEXT_BUFFER,
        },
        networking,
    },
    rvl_mem::IosAllocator,
    system::{
        alarm::{OSAlarm, OSInsertAlarm},
        ios::{IOS_CloseAsync, IOS_IoctlAsync, IOS_IoctlvAsync, IOS_OpenAsync},
        time::get_time_base,
    },
    utils::{console::Console, AlignedBuf},
};

pub struct IosAsyncContext {
    // if this is None, no async operation was in progress
    // otherwise contains the result
    pub result: Cell<Option<i32>>,
    pub fut:    Pin<Box<dyn Future<Output = ()>, IosAllocator>>,
}

impl IosAsyncContext {
    pub fn from_ctx<'a>(cx: &'a mut Context<'_>) -> &'a IosAsyncContext {
        unsafe { &*(cx.waker().as_raw().data() as *const IosAsyncContext) }
    }

    pub fn from_ptr<'a>(usr_data: *mut c_void) -> &'a IosAsyncContext {
        unsafe { &*(usr_data as *const IosAsyncContext) }
    }

    pub fn do_poll(this: *mut IosAsyncContext) {
        let cx = RawWaker::new(this as *const (), Waker::noop().as_raw().vtable());
        if let Poll::Ready(()) = unsafe {
            Pin::new(&mut (*this).fut).poll(&mut Context::from_waker(&Waker::from_raw(cx)))
        } {
            // feature is done, destruct it
            unsafe { Box::from_raw_in(this, IosAllocator) };
        }
    }
}

#[no_mangle]
extern "C" fn post_ios(result: c_int, usr_data: *mut c_void) {
    let ios_ctx = unsafe { &mut *(usr_data as *mut IosAsyncContext) };
    ios_ctx.result.set(Some(result));
    IosAsyncContext::do_poll(ios_ctx as *mut _);
}

#[no_mangle]
pub extern "C" fn run_net_init() {
    if unsafe { SOCK_STATUS.active } {
        return;
    }
    let net_fut = Box::pin_in(net_init_stuff(), IosAllocator);

    let ios_ctx = Box::new_in(
        IosAsyncContext {
            fut:    net_fut,
            result: Cell::new(None),
        },
        IosAllocator,
    );
    let ios_ctx = Box::leak(ios_ctx);
    IosAsyncContext::do_poll(ios_ctx as *mut _);
}

pub struct IosOpenFut<'a> {
    path: &'a CStr,
}

impl<'a> Future for IosOpenFut<'a> {
    type Output = Result<i32, i32>;
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        if let Some(result) = IosAsyncContext::from_ctx(cx).result.take() {
            if result < 0 {
                Poll::Ready(Err(result))
            } else {
                Poll::Ready(Ok(result))
            }
        } else {
            let result = unsafe {
                IOS_OpenAsync(
                    self.path.as_ptr(),
                    0,
                    post_ios,
                    cx.waker().as_raw().data() as *mut c_void,
                )
            };
            if result != 0 {
                Poll::Ready(Err(result))
            } else {
                Poll::Pending
            }
        }
    }
}

fn ios_open<'a>(path: &'a CStr) -> impl Future<Output = Result<i32, i32>> + 'a {
    IosOpenFut { path }
}

pub struct IosCloseFut {
    fd: c_int,
}

impl Future for IosCloseFut {
    type Output = Result<i32, i32>;
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        if let Some(result) = IosAsyncContext::from_ctx(cx).result.take() {
            if result < 0 {
                Poll::Ready(Err(result))
            } else {
                Poll::Ready(Ok(result))
            }
        } else {
            let result = unsafe {
                IOS_CloseAsync(self.fd, post_ios, cx.waker().as_raw().data() as *mut c_void)
            };
            if result != 0 {
                Poll::Ready(Err(result))
            } else {
                Poll::Pending
            }
        }
    }
}

fn ios_close<'a>(fd: c_int) -> impl Future<Output = Result<i32, i32>> + 'a {
    IosCloseFut { fd }
}

pub struct IosIoctlvFut {
    fd:      c_int,
    command: c_int,
    in_cnt:  c_int,
    out_cnt: c_int,
    ioctlv:  *mut c_void,
}

impl Future for IosIoctlvFut {
    type Output = Result<i32, i32>;
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        if let Some(result) = IosAsyncContext::from_ctx(cx).result.take() {
            if result < 0 {
                Poll::Ready(Err(result))
            } else {
                Poll::Ready(Ok(result))
            }
        } else {
            let result = unsafe {
                IOS_IoctlvAsync(
                    self.fd,
                    self.command,
                    self.in_cnt,
                    self.out_cnt,
                    self.ioctlv,
                    post_ios,
                    cx.waker().as_raw().data() as *mut c_void,
                )
            };
            if result != 0 {
                Poll::Ready(Err(result))
            } else {
                Poll::Pending
            }
        }
    }
}

pub struct IosIoctlFut {
    fd:      c_int,
    command: c_int,
    in_buf:  *mut c_void,
    in_len:  c_int,
    out_buf: *mut c_void,
    out_len: c_int,
}

impl Future for IosIoctlFut {
    type Output = Result<i32, i32>;
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        if let Some(result) = IosAsyncContext::from_ctx(cx).result.take() {
            // some commands have a non error response that is negative
            Poll::Ready(Ok(result))
        } else {
            let result = unsafe {
                IOS_IoctlAsync(
                    self.fd,
                    self.command,
                    self.in_buf,
                    self.in_len,
                    self.out_buf,
                    self.out_len,
                    post_ios,
                    cx.waker().as_raw().data() as *mut c_void,
                )
            };
            if result != 0 {
                Poll::Ready(Err(result))
            } else {
                Poll::Pending
            }
        }
    }
}

struct OSAlarmWithIosAsyncContext {
    alarm:   OSAlarm,
    context: *mut IosAsyncContext,
}

struct AlarmFut<'a> {
    os_alarm: &'a mut OSAlarmWithIosAsyncContext,
    timeout:  u64,
}

extern "C" fn alarm_callback(alarm: *mut OSAlarm) {
    let ios_ctx = unsafe { &mut *(*(alarm as *mut OSAlarmWithIosAsyncContext)).context };
    ios_ctx.result.set(Some(0));
    IosAsyncContext::do_poll(ios_ctx as *mut _);
}

impl<'a> Future for AlarmFut<'a> {
    type Output = ();
    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        if let Some(_) = IosAsyncContext::from_ctx(cx).result.take() {
            Poll::Ready(())
        } else {
            self.os_alarm.context = IosAsyncContext::from_ctx(cx) as *const _ as *mut _;
            unsafe {
                OSInsertAlarm(
                    self.os_alarm.borrow_mut() as *mut OSAlarmWithIosAsyncContext as *mut _,
                    self.timeout,
                    alarm_callback,
                )
            };
            Poll::Pending
        }
    }
}

async fn sleep(timeout: u64) {
    let mut alarm = OSAlarmWithIosAsyncContext {
        alarm:   OSAlarm::new(),
        context: null_mut(),
    };
    AlarmFut {
        os_alarm: &mut alarm,
        timeout,
    }
    .await
}

fn map_standard_result(result: Result<i32, i32>) -> Result<i32, i32> {
    if let Ok(value) = result {
        if value < 0 {
            return Err(value);
        }
    }
    result
}

#[repr(C, align(0x20))]
#[derive(Clone, Copy)]
struct SocketConnectParams {
    socket:     c_int,
    has_addr:   u32,
    sin_len:    u8,
    sin_family: u8,
    sin_port:   u16,
    sin_addr:   u32,
    sin_zero:   [u8; 20],
}

#[repr(C, align(0x20))]
#[derive(Default, Debug, Clone, Copy)]
struct SocketAddrIn {
    sin_len:    u8,
    sin_family: u8,
    sin_port:   u16,
    sin_addr:   u32,
}

struct ManageFd {
    fd: c_int,
}

impl ManageFd {
    async fn open() -> Result<Self, c_int> {
        ios_open(cstr!("/dev/net/ncd/manage"))
            .await
            .map(|fd| Self { fd })
    }

    async fn close(self) {
        // closing should really not fail
        let _ = ios_close(self.fd).await;
    }
}

struct TopFd {
    fd: c_int,
}

#[repr(C)]
#[derive(Clone, Copy)]
struct IosIoctlvEntry {
    data: *mut c_void,
    len:  u32,
}

impl Default for IosIoctlvEntry {
    fn default() -> Self {
        Self {
            data: null_mut(),
            len:  0,
        }
    }
}

#[repr(C, align(0x20))]
#[derive(Default, Debug, Clone, Copy)]
struct SocketSendToParams {
    socket:       c_int,
    flags:        u32,
    has_destaddr: u32,
    destaddr:     [u8; 28],
}

#[repr(C, align(0x20))]
#[derive(Default, Debug, Clone, Copy)]
struct SocketRecvFromParams {
    socket: c_int,
    flags:  u32,
}

#[repr(C, align(0x20))]
struct SendMessageReq {
    message_buf: AlignedBuf<SEND_BUFFER_SIZE>,
    params:      SocketSendToParams,
    ioctlv:      [IosIoctlvEntry; 2],
}

struct SendMessageFut<'a> {
    fd:      c_int,
    req:     Box<SendMessageReq, IosAllocator>,
    _marker: core::marker::PhantomData<&'a [u8]>,
}

impl<'a> SendMessageFut<'a> {
    fn new(
        fd: c_int,
        socket: c_int,
        message: &'a [u8],
        destaddr: Option<IpV4DestAddr>,
        seq_value: u16,
    ) -> Self {
        let mut req = Box::new_in(
            SendMessageReq {
                message_buf: AlignedBuf {
                    buf: [0u8; SEND_BUFFER_SIZE],
                },
                params:      SocketSendToParams {
                    socket,
                    flags: 0,
                    has_destaddr: destaddr.is_some().into(),
                    destaddr: destaddr.map(|a| a.to_array_28()).unwrap_or_default(),
                },
                ioctlv:      [IosIoctlvEntry::default(); 2],
            },
            IosAllocator,
        );
        let payload_len = message.len().min(SEND_BUFFER_SIZE - 2);
        req.message_buf.buf[0] = (seq_value >> 8) as u8;
        req.message_buf.buf[1] = seq_value as u8;
        req.message_buf.buf[2..payload_len + 2].copy_from_slice(&message[..payload_len]);
        req.ioctlv[0].data = req.message_buf.buf.as_mut_ptr().cast();
        req.ioctlv[0].len = (payload_len + 2) as u32;
        req.ioctlv[1].data = (&req.params as *const SocketSendToParams).cast_mut().cast();
        req.ioctlv[1].len = size_of_val(&req.params) as u32;

        Self {
            fd,
            req,
            _marker: core::marker::PhantomData,
        }
    }
}

impl<'a> Future for SendMessageFut<'a> {
    type Output = Result<i32, i32>;

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        if let Some(result) = IosAsyncContext::from_ctx(cx).result.take() {
            if result < 0 {
                Poll::Ready(Err(result))
            } else {
                Poll::Ready(Ok(result))
            }
        } else {
            let this = self.as_mut().get_mut();
            let result = unsafe {
                IOS_IoctlvAsync(
                    this.fd,
                    13, // IOCTL_SO_SENDTO
                    2,
                    0,
                    this.req.as_mut().ioctlv.as_mut_ptr().cast(),
                    post_ios,
                    cx.waker().as_raw().data() as *mut c_void,
                )
            };
            if result != 0 {
                Poll::Ready(Err(result))
            } else {
                Poll::Pending
            }
        }
    }
}

#[repr(C, align(0x20))]
struct ReceiveMessageReq {
    params:   SocketRecvFromParams,
    addr_buf: SocketAddrIn,
    ioctlv:   [IosIoctlvEntry; 3],
}

struct ReceiveMessageFut<'a> {
    fd:     c_int,
    req:    Box<ReceiveMessageReq, IosAllocator>,
    buffer: &'a mut [u8],
}

impl<'a> ReceiveMessageFut<'a> {
    fn new(fd: c_int, socket: c_int, buffer: &'a mut [u8]) -> Self {
        let mut req = Box::new_in(
            ReceiveMessageReq {
                params:   SocketRecvFromParams { socket, flags: 0 },
                addr_buf: SocketAddrIn::default(),
                ioctlv:   [IosIoctlvEntry::default(); 3],
            },
            IosAllocator,
        );
        req.ioctlv[0].data = (&req.params as *const SocketRecvFromParams)
            .cast_mut()
            .cast();
        req.ioctlv[0].len = size_of_val(&req.params) as u32;
        req.ioctlv[1].data = buffer.as_mut_ptr().cast();
        req.ioctlv[1].len = buffer.len() as u32;
        req.ioctlv[2].data = (&mut req.addr_buf as *mut SocketAddrIn).cast();
        req.ioctlv[2].len = size_of_val(&req.addr_buf) as u32;

        Self { fd, req, buffer }
    }
}

impl<'a> Future for ReceiveMessageFut<'a> {
    type Output = Result<i32, i32>;

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        if let Some(result) = IosAsyncContext::from_ctx(cx).result.take() {
            if result < 0 {
                Poll::Ready(Err(result))
            } else {
                Poll::Ready(Ok(result))
            }
        } else {
            let this = self.as_mut().get_mut();
            let result = unsafe {
                IOS_IoctlvAsync(
                    this.fd,
                    12, // IOCTL_SO_RECV
                    1,
                    2,
                    this.req.as_mut().ioctlv.as_mut_ptr().cast(),
                    post_ios,
                    cx.waker().as_raw().data() as *mut c_void,
                )
            };
            if result != 0 {
                Poll::Ready(Err(result))
            } else {
                Poll::Pending
            }
        }
    }
}

impl TopFd {
    async fn open() -> Result<Self, c_int> {
        ios_open(cstr!("/dev/net/ip/top"))
            .await
            .map(|fd| Self { fd })
    }

    async fn close(self) {
        // closing should really not fail
        let _ = ios_close(self.fd).await;
    }

    async fn socket_startup(&self) -> Result<i32, i32> {
        let result = IosIoctlFut {
            fd:      self.fd,
            command: 31, // IOCTL_SO_STARTUP
            in_buf:  null_mut(),
            in_len:  0,
            out_buf: null_mut(),
            out_len: 0,
        }
        .await;
        map_standard_result(result)
    }

    async fn get_host_id(&self) -> Result<i32, i32> {
        let result = IosIoctlFut {
            fd:      self.fd,
            command: 16, // IOCTL_SO_GETHOSTID
            in_buf:  null_mut(),
            in_len:  0,
            out_buf: null_mut(),
            out_len: 0,
        }
        .await;
        if matches!(result, Ok(0)) {
            return Err(0);
        }
        result
    }

    async fn create_tcp_socket(&self) -> Result<i32, i32> {
        let mut sock_init: AlignedBuf<3, i32> = AlignedBuf {
            buf: [
                2, // AF_INET
                1, // SOCK_STREAM
                0, // IPPROTO_IP
            ],
        };
        let result = IosIoctlFut {
            fd:      self.fd,
            command: 15, // IOCTL_SO_SOCKET
            in_buf:  sock_init.as_mut_ptr() as *mut _,
            in_len:  size_of_val(&sock_init) as i32,
            out_buf: null_mut(),
            out_len: 0,
        }
        .await;
        map_standard_result(result)
    }

    async fn create_udp_socket(&self) -> Result<i32, i32> {
        let mut sock_init: AlignedBuf<3, i32> = AlignedBuf {
            buf: [
                2, // AF_INET
                2, // SOCK_DGRAM
                0, // IPPROTO_IP
            ],
        };
        let result = IosIoctlFut {
            fd:      self.fd,
            command: 15, // IOCTL_SO_SOCKET
            in_buf:  sock_init.as_mut_ptr() as *mut _,
            in_len:  size_of_val(&sock_init) as i32,
            out_buf: null_mut(),
            out_len: 0,
        }
        .await;
        map_standard_result(result)
    }

    async fn close_socket(&self, socket_fd: i32) -> Result<(), i32> {
        let mut sock_fd = socket_fd;
        let result = IosIoctlFut {
            fd:      self.fd,
            command: 3, // IOCTL_SO_CLOSE
            in_buf:  &mut sock_fd as *mut i32 as *mut _,
            in_len:  size_of::<i32>() as i32,
            out_buf: null_mut(),
            out_len: 0,
        }
        .await;

        match map_standard_result(result) {
            Ok(_) => Ok(()),
            Err(e) => Err(e),
        }
    }

    async fn bind_socket(&self, socket: c_int, addr: c_uint, port: c_ushort) -> Result<i32, i32> {
        let mut params = SocketConnectParams {
            socket,
            has_addr: 1,
            sin_len: 8,
            sin_family: 2, // AF_INET
            sin_port: port,
            sin_addr: addr,
            sin_zero: Default::default(),
        };
        let result = IosIoctlFut {
            fd:      self.fd,
            command: 2, // IOCTL_SO_BIND
            in_buf:  &mut params as *mut SocketConnectParams as *mut _,
            in_len:  size_of_val(&params) as i32,
            out_buf: null_mut(),
            out_len: 0,
        }
        .await;
        map_standard_result(result)
    }
    // async fn set_socket_option(
    // &self,
    // socket: c_int,
    // level: u32,
    // optname: u32,
    // optval: &[u8],
    // ) -> Result<i32, i32> {
    // #[repr(C, align(0x20))]
    // struct SetSockOptParams {
    // socket:  u32,
    // level:   u32,
    // optname: u32,
    // optlen:  u32,
    // optval:  [u8; 20],
    // }
    //
    // let mut params = SetSockOptParams {
    // socket: socket as u32,
    // level,
    // optname,
    // optlen: optval.len() as u32,
    // optval: [0u8; 20],
    // };
    //
    // if !optval.is_empty() {
    // params.optval[..optval.len()].copy_from_slice(optval);
    // }
    //
    // let result = IosIoctlFut {
    // fd:      self.fd,
    // command: 4, // IOCTL_SO_SETSOCKOPT
    // in_buf:  &mut params as *mut SetSockOptParams as *mut _,
    // in_len:  size_of_val(&params) as i32,
    // out_buf: null_mut(),
    // out_len: 0,
    // }
    // .await;
    // map_standard_result(result)
    // }

    async fn connect_socket(
        &self,
        socket: c_int,
        addr: c_uint,
        port: c_ushort,
    ) -> Result<i32, i32> {
        let mut params = SocketConnectParams {
            socket,
            has_addr: 1,
            sin_len: 8,
            sin_family: 2, // AF_INET
            sin_port: port,
            sin_addr: addr,
            sin_zero: Default::default(),
        };
        let result = IosIoctlFut {
            fd:      self.fd,
            command: 4, // IOCTL_SO_CONNECT
            in_buf:  &mut params as *mut SocketConnectParams as *mut _,
            in_len:  size_of_val(&params) as i32,
            out_buf: null_mut(),
            out_len: 0,
        }
        .await;
        map_standard_result(result)
    }

    async fn listen_socket(&self, socket: c_int, backlog: c_uint) -> Result<i32, i32> {
        let mut params = AlignedBuf {
            buf: [socket as u32, backlog as u32],
        };
        let result = IosIoctlFut {
            fd:      self.fd,
            command: 10, // IOCTL_SO_LISTEN
            in_buf:  params.as_mut_ptr() as *mut _,
            in_len:  size_of_val(&params) as i32,
            out_buf: null_mut(),
            out_len: 0,
        }
        .await;
        map_standard_result(result)
    }

    async fn accept_socket(&self, socket: c_int) -> Result<(i32, SocketAddrIn), i32> {
        let mut params = AlignedBuf {
            buf: [socket as u32],
        };
        let mut addr_out = SocketAddrIn::default();
        let result = IosIoctlFut {
            fd:      self.fd,
            command: 1, // IOCTL_SO_ACCEPT
            in_buf:  params.as_mut_ptr() as *mut _,
            in_len:  size_of_val(&params) as i32,
            out_buf: &mut addr_out as *mut SocketAddrIn as *mut _,
            out_len: size_of_val(&addr_out) as i32,
        }
        .await;
        match result {
            Ok(val) => {
                if val < 0 {
                    Err(val)
                } else {
                    Ok((val, addr_out))
                }
            },
            Err(e) => Err(e),
        }
    }

    async fn send_message(
        &self,
        socket: c_int,
        message: &[u8],
        destaddr: Option<IpV4DestAddr>,
        seq_value: u16,
    ) -> Result<i32, i32> {
        let result = SendMessageFut::new(self.fd, socket, message, destaddr, seq_value).await;
        map_standard_result(result)
    }

    async fn receive_message(&self, socket: c_int, buffer: &mut [u8]) -> Result<i32, i32> {
        let result = ReceiveMessageFut::new(self.fd, socket, buffer).await;
        map_standard_result(result)
    }
}

#[derive(Copy, Clone)]
struct IpV4DestAddr {
    ip:   u32,
    port: u16,
}

impl IpV4DestAddr {
    fn to_array(&self) -> [u8; 8] {
        let port_b = self.port.to_be_bytes();
        let ip_b = self.ip.to_be_bytes();
        [
            8, 2, port_b[0], port_b[1], ip_b[0], ip_b[1], ip_b[2], ip_b[3],
        ]
    }

    fn to_array_28(&self) -> [u8; 28] {
        let port_b = self.port.to_be_bytes();
        let ip_b = self.ip.to_be_bytes();
        let mut buf = [0u8; 28];
        buf[0] = 8;
        buf[1] = 2;
        buf[2] = port_b[0];
        buf[3] = port_b[1];
        buf[4] = ip_b[0];
        buf[5] = ip_b[1];
        buf[6] = ip_b[2];
        buf[7] = ip_b[3];

        buf
    }
}

struct RequestFd {
    fd: c_int,
}

pub const CONNECTION_PORT: u16 = 43673;
const RECV_BUFFER_SIZE: usize = 1024;
const SEND_BUFFER_SIZE: usize = 512;

impl RequestFd {
    async fn open() -> Result<Self, c_int> {
        ios_open(cstr!("/dev/net/kd/request"))
            .await
            .map(|fd| Self { fd })
    }

    async fn close(self) {
        // closing should really not fail
        let _ = ios_close(self.fd).await;
    }

    async fn nwc_24_startup(&self) -> Result<i32, i32> {
        let mut cmd_buf: AlignedBuf<0x20> = AlignedBuf::default();
        let result = IosIoctlFut {
            fd:      self.fd,
            command: 6, // IOCTL_NWC24_STARTUP
            in_buf:  null_mut(),
            in_len:  0,
            out_buf: cmd_buf.as_mut_ptr() as *mut c_void,
            out_len: cmd_buf.len() as i32,
        }
        .await;
        map_standard_result(result)
    }
}

async fn net_init_stuff() {
    if let Err(e) = server_loop().await {
        println!("net init err: {e}");
        unsafe {
            SOCK_STATUS.active = false;
            SOCK_STATUS.last_error_code = e;
        }
    }
}

const HEADER_SIZE: usize = 3;

async fn server_loop() -> Result<(), i32> {
    unsafe {
        SOCK_STATUS.active = false;
        SOCK_STATUS.last_error_code = 0;
        SOCK_STATUS.progress = ServerProgress::None;
    };
    let request_fd = RequestFd::open().await?;
    println!("req open");
    let _ = request_fd.nwc_24_startup().await;
    request_fd.close().await;
    println!("nwc24");
    let top_fd = TopFd::open().await?;
    top_fd.socket_startup().await?;
    println!("sock start");
    let ip = top_fd.get_host_id().await?;
    let ip = Ipv4Addr::from(ip as u32);
    unsafe { SOCK_STATUS.ip = ip };
    println!("ip: {}", ip);
    let sock = top_fd.create_udp_socket().await?;
    println!("udp sock create");
    unsafe {
        SOCK_STATUS.progress = ServerProgress::CreatedUDP;
        if let Some(s) = SOCK_STATUS.last_opened_socket {
            top_fd.close_socket(s).await?;
        }
        SOCK_STATUS.last_opened_socket = Some(sock);
    };

    top_fd.bind_socket(sock, ip.into(), CONNECTION_PORT).await?;
    println!("udp sock bound");
    unsafe {
        SOCK_STATUS.progress = ServerProgress::BoundSocket;
        SOCK_STATUS.active = true;
    };
    println!("waiting for UDP messages...");
    let mut buffer = AlignedBuf {
        buf: [0u8; RECV_BUFFER_SIZE],
    };

    loop {
        let readres = top_fd.receive_message(sock, &mut buffer.buf).await;
        match readres {
            Ok(byteread) => {
                let bytes_received = byteread as usize;
                let client_addr = unsafe { SOCK_STATUS.client_conn };

                if bytes_received >= HEADER_SIZE {
                    let seq = u16::from_be_bytes(buffer[0..2].try_into().unwrap());
                    let msg_type = buffer[2];
                    println!("recv command {}", msg_type);
                    // unsafe { SOCK_STATUS.num_requests += 1 }
                    if let Some(_) = client_addr {
                        match msg_type {
                            0 => {
                                // ESTABLISH: 0x00 - [IP bytes] - [Port bytes]
                                println!("client connected");
                                if bytes_received == HEADER_SIZE + 6 {
                                    let ip = u32::from_be_bytes(buffer[HEADER_SIZE..HEADER_SIZE + 4].try_into().unwrap());
                                    let port = u16::from_be_bytes(buffer[HEADER_SIZE + 4..HEADER_SIZE + 6].try_into().unwrap());
                                    let dest_addr = IpV4DestAddr { ip, port };
                                    unsafe {
                                        SOCK_STATUS.client_conn = Some(dest_addr);
                                        SOCK_STATUS.progress =
                                            ServerProgress::ConnectionEstablished;
                                        SOCK_STATUS.show_ip = false;
                                    }

                                    // acknowledgement message for the AP client
                                    let _ = top_fd
                                        .send_message(
                                            sock,
                                            &[msg_type],
                                            Some(dest_addr),
                                            seq
                                        )
                                        .await;
                                }
                            },
                            1 => {
                                // READ_BYTES: 0x01 - [Address bytes] - [Length bytes]
                                if bytes_received >= 10 {
                                    let addr =
                                        usize::from_be_bytes(buffer[HEADER_SIZE..HEADER_SIZE + 4].try_into().unwrap());
                                    let num_to_read =
                                        u32::from_be_bytes(buffer[HEADER_SIZE + 4..HEADER_SIZE + 8].try_into().unwrap())
                                            as usize;
                                    if addr != 0 {
                                        if let Some(data) =
                                            read_bytes_from_address(addr, num_to_read, true)
                                        {
                                            // forward requested data
                                            let _ =
                                                top_fd.send_message(sock, data, client_addr, seq).await;
                                        }
                                    }
                                }
                            },
                            /*
                            2 => {
                                // WRITE_BYTES: 0x02 - [Address bytes] - [Length bytes] - [Content]
                                // - [Checksum]
                                if bytes_received >= 10 {
                                    let addr = u32::from_be_bytes(buffer[1..5].try_into().unwrap());
                                    let num_to_write =
                                        u32::from_be_bytes(buffer[5..9].try_into().unwrap())
                                            as usize;

                                    let checksum = buffer[bytes_received - 1] as u32;
                                    let act_sum = buffer[0..bytes_received - 1]
                                        .iter()
                                        .map(|x| *x as u32)
                                        .sum::<u32>()
                                        & 0xFF;

                                    if addr != 0
                                        && checksum == act_sum
                                        && bytes_received >= 9 + num_to_write
                                    {
                                        write_bytes_to_address(addr, &buffer[9..9 + num_to_write]);
                                        // acknowledge
                                        let _ =
                                            top_fd.send_message(sock, &[2u8], client_addr).await;
                                    }
                                }
                            },
                            */
                            3 => {
                                // REQ_SCENE_FLAGS: 0x03
                                let _ = top_fd.send_message(sock, &file_manager::get_current_scene_flags(), client_addr, seq).await;
                            },
                            4 => {
                                // REQ_STORY_FLAGS: 0x04
                                let _ = top_fd.send_message(sock, &file_manager::get_current_story_flags(), client_addr, seq).await;
                            },
                            5 => {
                                // DISCONNECT: 0x05 - send acknowledgment and display IP for
                                // reconnection
                                println!("client signaled dc");
                                let _ = top_fd.send_message(sock, &[msg_type], client_addr, seq).await;
                                unsafe {
                                    SOCK_STATUS.client_conn = None;
                                    SOCK_STATUS.progress = ServerProgress::BoundSocket;
                                    SOCK_STATUS.show_ip = true;
                                }
                            },
                            6 => {
                                // REQ_SLOT_NAME
                                let _ = top_fd
                                    .send_message(
                                        sock,
                                        unsafe { &ARCHIPELAGO_SLOT_NAME },
                                        client_addr,
                                        seq
                                    )
                                    .await;
                            },
                            7 => {
                                // REQ_STATUS
                                let stat = APStatusReport::new();
                                let stat_bytes = unsafe {
                                    core::slice::from_raw_parts(
                                        (&stat as *const APStatusReport) as *const u8,
                                        size_of_val(&stat),
                                    )
                                };
                                let _ = top_fd.send_message(sock, stat_bytes, client_addr, seq).await;
                            },
                            8 => {
                                // GIVE_ITEM
                                if bytes_received == HEADER_SIZE + 1 {
                                    let item_id = buffer[HEADER_SIZE];
                                    multiworld::try_place_item(item_id);
                                    // recalculate status (incl. new expected_index)
                                    let stat = APStatusReport::new();
                                    let stat_bytes = unsafe {
                                        core::slice::from_raw_parts(
                                            (&stat as *const APStatusReport) as *const u8,
                                            size_of_val(&stat),
                                        )
                                    };
                                    let _ =
                                        top_fd.send_message(sock, stat_bytes, client_addr, seq).await;
                                }
                            },
                            9 => {
                                // KILL_LINK
                                let res = if multiworld::kill_link() { 1u8 } else { 0u8 };
                                let _ = top_fd.send_message(sock, &[res], client_addr, seq).await;
                            },
                            10 => {
                                // DEPLETE_STAMINA
                                let res = if multiworld::deplete_stamina() {
                                    1u8
                                } else {
                                    0u8
                                };
                                let _ = top_fd.send_message(sock, &[res], client_addr, seq).await;
                            },
                            11 => {
                                // WRITE_TO_TEXT_BUFFER
                                let text_buf = unsafe { ARCHIPELAGO_TEXT_BUFFER.as_mut() };
                                let copy_len =
                                    core::cmp::min(bytes_received - HEADER_SIZE, text_buf.len() - HEADER_SIZE);
                                text_buf.fill(0);
                                unsafe {
                                    copy_nonoverlapping(
                                        buffer[HEADER_SIZE..HEADER_SIZE + copy_len].as_ptr(),
                                        text_buf.as_mut_ptr(),
                                        copy_len,
                                    );
                                }
                                let _ = top_fd.send_message(sock, &[msg_type], client_addr, seq).await;
                            },
                            _ => {
                                println!("unknown command: {}", buffer[0]);
                            },
                        }
                    } else {
                        match buffer[0] {
                            0 => {
                                // ESTABLISH: 0x00 - [IP bytes] - [Port bytes]
                                println!("client connected");
                                if bytes_received == HEADER_SIZE + 6 {
                                    let ip = u32::from_be_bytes(
                                        buffer[HEADER_SIZE..HEADER_SIZE + 4].try_into().unwrap(),
                                    );
                                    let port = u16::from_be_bytes(
                                        buffer[HEADER_SIZE + 4..HEADER_SIZE + 6]
                                            .try_into()
                                            .unwrap(),
                                    );
                                    let dest_addr = IpV4DestAddr { ip, port };
                                    unsafe {
                                        SOCK_STATUS.client_conn = Some(dest_addr);
                                        SOCK_STATUS.progress =
                                            ServerProgress::ConnectionEstablished;
                                        SOCK_STATUS.show_ip = false;
                                    }

                                    // acknowledgement message for the AP client
                                    let _ = top_fd
                                        .send_message(sock, &[msg_type], Some(dest_addr), seq)
                                        .await;
                                }
                            },
                            _ => {
                                println!(
                                    "unknown command (connection must be established first): {}",
                                    buffer[0]
                                );
                            },
                        }
                    }
                }
            },
            Err(e) => {
                println!("error when reading: {:?}", readres);
                if e == -8 {
                    // Bad FD, caused by shutdown, so exit loop
                    return Err(e);
                }
            },
        }

        buffer.fill(0);
        // need to yield so the thread doesn't get too busy and crash on console
        crate::rvl_os::yield_thread();
    }
    Ok(())
}

#[derive(PartialEq, Eq)]
pub enum ServerProgress {
    None,
    CreatedUDP,
    BoundSocket,
    ConnectionEstablished,
}

pub struct APSocketStatus {
    pub ip:                 Ipv4Addr,
    pub client_conn:        Option<IpV4DestAddr>,
    pub active:             bool,
    pub show_ip:            bool,
    pub last_error_code:    i32,
    pub progress:           ServerProgress,
    pub last_opened_socket: Option<i32>,
    // pub num_requests:    u32,
}

pub static mut SOCK_STATUS: APSocketStatus = APSocketStatus {
    ip:                 Ipv4Addr::new(0, 0, 0, 0),
    client_conn:        None,
    active:             false,
    show_ip:            true,
    last_error_code:    0,
    progress:           ServerProgress::None,
    last_opened_socket: None,
    // num_requests:    0,
};
