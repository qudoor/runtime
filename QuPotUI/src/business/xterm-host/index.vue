<template>
  <div>
    <div style="position: absolute;right: 10px;z-index: 200">
      <!-- <el-button size="large" icon="el-icon-video-play" @click="initwebsocket()" style="float: right;">
      </el-button> -->
    </div>
    <div>
      <div id="terminal-container"></div>
    </div>
  </div>
</template>

<script>
import "xterm/css/xterm.css"
import { Terminal } from "xterm"

export default {
  name: "xTerm",
  data() {
    return {
      term: Terminal,
      isRun: true,
      timer: null,
    }
  },
  methods: {
    get_connect_info() {
      let host = this.$route.query.ip,
        port = this.$route.query.port,
        credentialId = this.$route.query.credentialId

      console.log('credentialId :', credentialId)
      return "host=" + host + "&port=" + port + "&credentialId=" + credentialId
    },
    get_term_size() {
      let init_width = 9;
      let init_height = 17;

      let windows_width = window.innerWidth;
      let windows_height = window.innerHeight;

      return {
        cols: Math.floor(windows_width / init_width),
        rows: Math.floor(windows_height / init_height),
      }
    },
    initwebsocket() {
      let _this = this
      let cols = _this.get_term_size().cols;
      let rows = _this.get_term_size().rows;
      let connect_info = this.get_connect_info();

      let term = new Terminal(
        {
          cols: cols,
          rows: rows,
          useStyle: true,
          cursorBlink: true
        }
      ),
        protocol = (location.protocol === 'https:') ? 'wss://' : 'ws://',
        // socketURL = protocol + location.hostname + ((location.port) ? (':' + location.port) : '') +
        //   '/webssh/?' + connect_info + '&width=' + cols + '&height=' + rows;
        socketURL = protocol + location.host + "/ws/webssh/?" + connect_info + '&width=' + cols + '&height=' + rows;

      let sock;
      console.log('socketURL:', socketURL)
      sock = new WebSocket(socketURL);

      // 打开 websocket 连接, 打开 web 终端
      sock.addEventListener('open', function () {
        // $('#form').addClass('hide');
        // $('#django-webssh-terminal').removeClass('hide');
        term.open(document.getElementById('terminal-container'));
      });

      // 读取服务器端发送的数据并写入 web 终端
      sock.addEventListener('message', function (recv) {
        let data = JSON.parse(recv.data);
        let message = data.message;
        let status = data.status;
        if (status === 0) {
          term.write(message)
        } else {
          window.location.reload()
        }
      });

      /*
      * status 为 0 时, 将用户输入的数据通过 websocket 传递给后台, data 为传递的数据, 忽略 cols 和 rows 参数
      * status 为 1 时, resize pty ssh 终端大小, cols 为每行显示的最大字数, rows 为每列显示的最大字数, 忽略 data 参数
      */
      let message = { 'status': 0, 'data': null, 'cols': null, 'rows': null };

      // 向服务器端发送数据
      term.onData(function (data) {
        message['status'] = 0;
        message['data'] = data;
        let send_data = JSON.stringify(message);
        sock.send(send_data)
      });

      // 监听浏览器窗口, 根据浏览器窗口大小修改终端大小
      window.addEventListener("resize", function () {
        let cols = _this.get_term_size().cols;
        let rows = _this.get_term_size().rows;
        message['status'] = 1;
        message['cols'] = cols;
        message['rows'] = rows;
        let send_data = JSON.stringify(message);
        sock.send(send_data);
        term.resize(cols, rows)
      })

      // 监听可能发生的错误
      sock.addEventListener('error', function (event) {
        console.log('WebSocket error: ', event);
      });
    },
    changeMode() {
      this.isRun = !this.isRun
    },
  },
  destroyed() {
    clearInterval(this.timer)
    this.timer = null
  },
  mounted() {
    this.initwebsocket()
  },
}
</script>
