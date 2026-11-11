import hashlib, hmac, html, json, os, re, secrets, subprocess, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http import cookies
from urllib.parse import parse_qs, urlsplit
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(os.environ.get("APP_DATA","/data"))
ROOT.mkdir(parents=True,exist_ok=True)
PASSWORD=ROOT/"admin-password.txt"; CONFIG=ROOT/"config.json"; STATE=ROOT/"state.json"
if not PASSWORD.exists():
    PASSWORD.write_text(secrets.token_urlsafe(24)+"\n")
    PASSWORD.chmod(0o600)
DEFAULT={"claude_enabled":False,"codex_enabled":False,"interval_minutes":300,
 "proxy_url":"http://127.0.0.1:7890","claude_model":"haiku","codex_model":"","codex_effort":"low"}
def load(path,default):
    try: return json.loads(path.read_text())
    except (ValueError,FileNotFoundError): return default.copy()
def save(path,data):
    p=path.with_suffix(".tmp")
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2))
    p.chmod(0o600);p.replace(path)
cfg={**DEFAULT,**load(CONFIG,{})}
status=load(STATE,{"claude":{"state":"never"},"codex":{"state":"never"}})
lock=threading.RLock();sessions={};running=set()
def allowed_proxy(s):
    if not s:return True
    if len(s)>200 or any(c in s for c in "@#\\\n\r"):return False
    try:
        p=urlsplit(s)
        return p.scheme in ("http","https") and bool(p.hostname) and bool(p.port) and p.path in ("","/") and not p.query and not p.fragment
    except ValueError:return False
def env_for(kind,settings):
    env={k:v for k,v in os.environ.items() if k not in
      ("ANTHROPIC_API_KEY","ANTHROPIC_AUTH_TOKEN","OPENAI_API_KEY","CLAUDE_CODE_OAUTH_TOKEN")}
    home=ROOT/("home-"+kind);home.mkdir(mode=0o700,exist_ok=True)
    env["HOME"]=str(home);env["XDG_CONFIG_HOME"]=str(home/".config")
    env["DISABLE_AUTOUPDATER"]="1";env["DISABLE_TELEMETRY"]="1"
    for key in ("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","http_proxy","https_proxy","all_proxy"):env.pop(key,None)
    proxy=settings["proxy_url"]
    if proxy:
        for key in ("HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy"):env[key]=proxy
        if proxy.startswith("socks5"):env["ALL_PROXY"]=env["all_proxy"]=proxy
    if kind=="claude":
        token=ROOT/"claude-oauth-token"
        if token.is_file():env["CLAUDE_CODE_OAUTH_TOKEN"]=token.read_text().strip()
    return env
def execute(kind):
    with lock:
        if kind in running:return
        running.add(kind)
        status[kind]={"state":"running","at":datetime.now(timezone.utc).isoformat()};save(STATE,status)
        options=cfg.copy()
    try:
        if kind=="claude":
            cmd=["claude","-p","hi","--model","haiku","--max-turns","1","--tools","","--output-format","text"]
        else:
            cmd=["codex","exec","hi","--sandbox","read-only","--skip-git-repo-check","--ephemeral",
                 "-c","model_reasoning_effort="+options["codex_effort"]]
            if options["codex_model"]:cmd[2:2]=["--model",options["codex_model"]]
        result=subprocess.run(cmd,env=env_for(kind,options),cwd="/tmp",capture_output=True,timeout=120,check=False)
        outcome="success" if result.returncode==0 and result.stdout.strip() else "failed"
    except (OSError,subprocess.TimeoutExpired):outcome="failed"
    with lock:
        status[kind]={"state":outcome,"at":datetime.now(timezone.utc).isoformat()}
        running.discard(kind);save(STATE,status)
def schedule():
    last={"claude":0,"codex":0}
    while True:
        time.sleep(20)
        with lock:settings=cfg.copy()
        now=time.time()
        for kind in ("claude","codex"):
            if settings[kind+"_enabled"] and now-last[kind]>=settings["interval_minutes"]*60:
                last[kind]=now
                threading.Thread(target=execute,args=(kind,),daemon=True).start()
CSS="""body{background:#f3f6fa;color:#203047;font:15px system-ui;margin:0}main{max-width:820px;margin:35px auto;padding:0 18px}section{background:white;padding:23px;border:1px solid #dce3ec;border-radius:12px;margin:15px 0}h1{font-size:26px}h2{font-size:18px}label{display:block;font-weight:600;margin:14px 0 7px}input[type=text],input[type=password],input[type=number],select{box-sizing:border-box;width:100%;padding:10px;border-radius:6px;border:1px solid #abbacb}button{background:#16539c;border:0;border-radius:7px;padding:10px 16px;color:white;cursor:pointer}.grid{display:grid;grid-template-columns:1fr 1fr;gap:15px}small{color:#617086}code{background:#eef2f6;padding:3px;border-radius:4px}@media(max-width:600px){.grid{grid-template-columns:1fr}}"""
def page(body):return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NAS AI 用量管理</title><style>'+CSS+'</style><main>'+body+'</main></html>'
def esc(s):return html.escape(str(s),quote=True)
class Web(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,code,text,cookie=None):
        data=text.encode()
        self.send_response(code)
        for k,v in {"Content-Type":"text/html; charset=utf-8","Content-Length":str(len(data)),
          "Cache-Control":"no-store","X-Content-Type-Options":"nosniff","X-Frame-Options":"DENY",
          "Referrer-Policy":"no-referrer","Content-Security-Policy":"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'"}.items():
            self.send_header(k,v)
        if cookie:self.send_header("Set-Cookie",cookie)
        self.end_headers();self.wfile.write(data)
    def session(self):
        jar=cookies.SimpleCookie()
        try:jar.load(self.headers.get("Cookie",""))
        except cookies.CookieError:return None
        sid=jar.get("sid")
        if not sid:return None
        s=sessions.get(sid.value)
        return s if s and s["expires"]>time.time() else None
    def form(self):
        try:n=int(self.headers.get("Content-Length","0"))
        except ValueError:return None
        if n<0 or n>8192:return None
        return {k:v[0] for k,v in parse_qs(self.rfile.read(n).decode(),keep_blank_values=True).items()}
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=="/health":return self.send(200,"ok")
        if path!="/":return self.send(404,page("Not found"))
        s=self.session()
        if not s:
            return self.send(200,page('<h1>NAS AI 用量管理</h1><section><form method="post" action="/login"><label>管理员密码</label><input type="password" name="password" required><p><button>登录</button></p></form><small>初始密码：docker compose exec dashboard cat /data/admin-password.txt</small></section>'))
        token=esc(s["csrf"])
        with lock:settings=cfg.copy();records=status.copy()
        b='<h1>AI 五小时窗口管理</h1><p>真实请求会消耗订阅额度，不保证刷新窗口。</p>'
        b+='<section><h2>运行状态</h2><div class="grid">'
        for kind in ("claude","codex"):
            rec=records.get(kind,{"state":"never"})
            b+='<div><b>'+kind.title()+'</b><p>'+esc(rec.get("state","never"))+'</p><small>'+esc(rec.get("at","未运行"))+'</small><form method="post" action="/run"><input type="hidden" name="csrf" value="'+token+'"><input type="hidden" name="provider" value="'+kind+'"><p><button>手动请求一次</button></p></form></div>'
        b+='</div></section><section><h2>配置</h2><form method="post" action="/settings"><input type="hidden" name="csrf" value="'+token+'">'
        for kind in ("claude","codex"):
            checked=" checked" if settings[kind+"_enabled"] else ""
            b+='<label><input type="checkbox" name="'+kind+'_enabled"'+checked+'>启用 '+kind.title()+' 定时请求</label>'
        b+='<label>执行间隔（分钟）</label><input type="number" min="60" max="10080" name="interval_minutes" value="'+str(settings["interval_minutes"])+'">'
        b+='<label>Clash HTTP / mixed 代理（NAS 本机地址）</label><input type="text" name="proxy_url" placeholder="http://127.0.0.1:7890" value="'+esc(settings["proxy_url"])+'"><small>Dashboard 与 Mihomo 均使用 host 网络；此处填写 NAS 本机代理监听地址。</small>'
        b+='<label>Codex 模型（留空使用默认）</label><input type="text" name="codex_model" value="'+esc(settings["codex_model"])+'">'
        b+='<label>Codex 推理强度</label><select name="codex_effort">'+''.join('<option value="'+v+'"'+(" selected" if settings["codex_effort"]==v else "")+'>'+v+'</option>' for v in ("minimal","low","medium"))+'</select><p>Claude 固定使用 Haiku，内容为 hi。</p><button>保存配置</button></form></section>'
        b+='<section><h2>认证（仅 NAS 终端）</h2><p>Codex：<code>docker compose exec dashboard sh /opt/app/scripts/codex-login.sh</code></p><p>Claude：本地 <code>claude setup-token</code> 后，将 Token 写入 <code>/data/claude-oauth-token</code>（权限 600）。网页不接收 OAuth Token。</p></section>'
        b+='<form method="post" action="/logout"><input type="hidden" name="csrf" value="'+token+'"><button>退出登录</button></form><p><small>默认仅绑定 NAS 本机。远程访问推荐 SSH 隧道或 VPN，请勿直接暴露公网。</small></p>'
        self.send(200,page(b))
    def do_POST(self):
        path=urlsplit(self.path).path;f=self.form()
        if f is None:return self.send(400,page("Bad request"))
        if path=="/login":
            ok=hmac.compare_digest(f.get("password","").encode(),PASSWORD.read_text().strip().encode())
            if not ok:time.sleep(.8);return self.send(403,page('密码错误 <a href="/">返回</a>'))
            sid=secrets.token_urlsafe(32)
            sessions[sid]={"csrf":secrets.token_urlsafe(32),"expires":time.time()+28800}
            secure="; Secure" if os.environ.get("COOKIE_SECURE")=="1" else ""
            return self.send(200,page('<a href="/">进入控制台</a>'),"sid="+sid+"; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800"+secure)
        s=self.session();origin=self.headers.get("Origin")
        if not s or not hmac.compare_digest(f.get("csrf",""),s["csrf"]) or (origin and urlsplit(origin).netloc!=self.headers.get("Host")) or self.headers.get("Sec-Fetch-Site","same-origin") not in ("none","same-origin"):
            return self.send(403,page("CSRF protection"))
        if path=="/settings":
            try:minutes=int(f.get("interval_minutes","0"))
            except ValueError:minutes=0
            proxy=f.get("proxy_url","").strip();model=f.get("codex_model","").strip();effort=f.get("codex_effort","")
            if not 60<=minutes<=10080 or not allowed_proxy(proxy) or not re.fullmatch(r"[A-Za-z0-9_.-]{0,80}",model) or effort not in ("minimal","low","medium"):
                return self.send(400,page("无效的配置"))
            with lock:
                cfg.update({"claude_enabled":"claude_enabled" in f,"codex_enabled":"codex_enabled" in f,"interval_minutes":minutes,"proxy_url":proxy,"codex_model":model,"codex_effort":effort})
                save(CONFIG,cfg)
        elif path=="/run":
            kind=f.get("provider","")
            if kind not in ("claude","codex"):return self.send(400,page("Unknown provider"))
            threading.Thread(target=execute,args=(kind,),daemon=True).start()
        elif path=="/logout":
            jar=cookies.SimpleCookie();jar.load(self.headers.get("Cookie",""))
            if jar.get("sid"):sessions.pop(jar["sid"].value,None)
            return self.send(200,page('<a href="/">已退出</a>'),"sid=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0")
        else:return self.send(404,page("Not found"))
        self.send(200,page('<p>操作已接受。<a href="/">返回控制台</a></p>'))
if __name__=="__main__":
    threading.Thread(target=schedule,daemon=True).start()
    ThreadingHTTPServer((os.environ.get("BIND_HOST","127.0.0.1"),int(os.environ.get("PORT","8787"))),Web).serve_forever()
