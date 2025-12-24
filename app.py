import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from io_manager import IOManager

app = FastAPI(title="I/O Panel (Raspberry Pi 5)")

DEFAULT_CONFIG_PATH = os.environ.get("IO_CONFIG_PATH", "config/io.yaml")

io = IOManager(config_path=DEFAULT_CONFIG_PATH)


class SetOutputBody(BaseModel):
    state: bool

class ReloadBody(BaseModel):
    config_path: str | None = None


PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>I/O Panel</title>
  <style>
    :root { color-scheme: light; }
    body { font-family: Arial, sans-serif; max-width: 960px; margin: 30px auto; padding: 0 16px; }
    h1 { margin-bottom: 8px; }
    .top { display:flex; gap:12px; align-items:center; flex-wrap: wrap; }
    .actions { display:flex; gap:8px; align-items:center; flex-wrap: wrap; }
    button { padding: 10px 14px; font-size: 14px; cursor: pointer; border-radius: 8px; border:1px solid #ddd; background:#f8f8f8; }
    button.primary { background:#1c6ee8; color:white; border-color:#1c6ee8; }
    button:disabled { opacity: 0.7; cursor: not-allowed; }
    .box { margin-top: 14px; padding: 12px; border: 1px solid #ddd; border-radius: 10px; background:white; box-shadow:0 1px 2px rgba(0,0,0,0.04); }
    .grid { display:grid; grid-template-columns: 1fr 140px 160px; gap:10px; align-items:center; }
    .muted { color:#555; font-size: 13px; }
    .err { color:#b00020; white-space: pre-wrap; }
    .pill { display:inline-block; padding:2px 8px; border:1px solid #ccc; border-radius:999px; font-size:12px; }
    input[type=text] { padding:8px 10px; border:1px solid #ccc; border-radius:8px; min-width: 260px; }
    .status-row { display:flex; gap:10px; align-items:center; flex-wrap: wrap; }
    .kval { display:flex; gap:6px; align-items:center; }
    .chip { padding:4px 8px; background:#f1f4f9; border-radius:8px; border:1px solid #e0e5ed; font-size:13px; }
    .layout { display:grid; grid-template-columns: 2fr 1fr; gap:14px; }
    @media (max-width: 820px){ .layout { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <h1>Panel de Entradas / Salidas</h1>

  <div class="box">
    <div class="status-row">
      <div class="kval"><span class="muted">Backend:</span> <span class="pill" id="backend">(backend)</span></div>
      <div class="kval"><span class="muted">Uptime:</span> <span id="uptime">-</span></div>
      <div class="kval"><span class="muted">Config actual:</span> <span class="chip" id="config-path">-</span></div>
    </div>
    <div class="top" style="margin-top:12px;">
      <div class="actions">
        <button class="primary" onclick="reloadConfig()">Recargar config</button>
        <button onclick="refresh()">Actualizar</button>
      </div>
      <div class="actions">
        <label class="muted">Archivo de configuración:</label>
        <input type="text" id="config-input" value="config/io.yaml" />
      </div>
    </div>
  </div>

  <div class="layout">
    <div class="box">
      <div class="muted">Salidas (outputs)</div>
      <div id="outputs"></div>
    </div>

    <div class="box">
      <div class="muted">Entradas (inputs)</div>
      <div id="inputs"></div>
    </div>
  </div>

  <div class="box">
    <div class="muted">Diagnóstico</div>
    <div id="diag"></div>
    <div id="err" class="err"></div>
  </div>

<script>
async function apiGet(url){
  const r = await fetch(url);
  const data = await r.json();
  if (!r.ok) throw data;
  return data;
}
async function apiPost(url, body){
  const r = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body || {})
  });
  const data = await r.json();
  if (!r.ok) throw data;
  return data;
}

function renderOutputs(outputs){
  const root = document.getElementById('outputs');
  root.innerHTML = '';
  const grid = document.createElement('div');
  grid.className = 'grid';

  // header
  grid.innerHTML += '<div class="muted">Nombre</div><div class="muted">Estado</div><div class="muted">Acción</div>';

  for (const o of outputs){
    const name = document.createElement('div');
    name.textContent = `${o.name} (BCM ${o.bcm})`;

    const st = document.createElement('div');
    st.textContent = o.is_on ? 'ENCENDIDO' : 'APAGADO';

    const actions = document.createElement('div');
    const btn = document.createElement('button');
    btn.textContent = o.is_on ? 'Apagar' : 'Encender';
    btn.onclick = async () => {
      await apiPost(`/outputs/${o.id}`, {state: !o.is_on});
      await refresh();
    };
    actions.appendChild(btn);

    grid.appendChild(name);
    grid.appendChild(st);
    grid.appendChild(actions);
  }

  root.appendChild(grid);
}

function renderInputs(inputs){
  const root = document.getElementById('inputs');
  root.innerHTML = '';
  const grid = document.createElement('div');
  grid.className = 'grid';

  grid.innerHTML += '<div class="muted">Nombre</div><div class="muted">Valor</div><div class="muted">BCM</div>';

  for (const i of inputs){
    const name = document.createElement('div');
    name.textContent = i.name;

    const val = document.createElement('div');
    val.textContent = i.value ? 'ON' : 'OFF';

    const bcm = document.createElement('div');
    bcm.textContent = i.bcm;

    grid.appendChild(name);
    grid.appendChild(val);
    grid.appendChild(bcm);
  }

  root.appendChild(grid);
}

async function refresh(){
  try{
    const io = await apiGet('/io');
    document.getElementById('backend').textContent = io.backend;
    document.getElementById('config-path').textContent = io.config_path;
    document.getElementById('config-input').value = io.config_path;
    document.getElementById('diag').textContent = `Uptime: ${io.uptime_seconds}s`;
    document.getElementById('uptime').textContent = `${io.uptime_seconds}s`;
    document.getElementById('err').textContent = io.error ? io.error : '';
    renderOutputs(io.outputs || []);
    renderInputs(io.inputs || []);
  }catch(e){
    document.getElementById('err').textContent = JSON.stringify(e);
  }
}

async function reloadConfig(){
  const btns = document.querySelectorAll('button');
  btns.forEach(b => b.disabled = true);
  try{
    const configPath = document.getElementById('config-input').value;
    await apiPost('/reload', {config_path: configPath});
    await refresh();
  }catch(e){
    document.getElementById('err').textContent = JSON.stringify(e);
  }finally{
    btns.forEach(b => b.disabled = false);
  }
}

refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE

@app.get("/io")
def get_io():
    return JSONResponse({
        "backend": "gpiozero+lgpio(chip=0)",
        "uptime_seconds": io.uptime_seconds(),
        "error": io.last_error(),
        "outputs": io.list_outputs(),
        "inputs": io.list_inputs(),
        "config_path": str(io.config_path),
    })

@app.post("/outputs/{output_id}")
def set_output(output_id: str, body: SetOutputBody):
    try:
        is_on = io.set_output(output_id, body.state)
        return JSONResponse({"ok": True, "id": output_id, "is_on": is_on})
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))

@app.post("/reload")
def reload_config(body: ReloadBody):
    try:
        io.reload(body.config_path)
        return JSONResponse({"ok": True, "config_path": str(io.config_path), "error": io.last_error()})
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))
