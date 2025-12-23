from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from io_manager import IOManager

app = FastAPI(title="I/O Panel (Raspberry Pi 5)")

io = IOManager(config_path="config/io.yaml")


class SetOutputBody(BaseModel):
    state: bool


PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>I/O Panel</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 760px; margin: 30px auto; }
    .top { display:flex; gap:12px; align-items:center; }
    button { padding: 10px 14px; font-size: 14px; cursor: pointer; }
    .box { margin-top: 14px; padding: 12px; border: 1px solid #ddd; border-radius: 10px; }
    .grid { display:grid; grid-template-columns: 1fr 140px 140px; gap:10px; align-items:center; }
    .muted { color:#555; font-size: 13px; }
    .err { color:#b00020; white-space: pre-wrap; }
    .pill { display:inline-block; padding:2px 8px; border:1px solid #ccc; border-radius:999px; font-size:12px; }
  </style>
</head>
<body>
  <h1>Panel de Entradas / Salidas</h1>

  <div class="top">
    <button onclick="reloadConfig()">Recargar configuración</button>
    <button onclick="refresh()">Actualizar</button>
    <span class="pill" id="backend">(backend)</span>
  </div>

  <div class="box">
    <div class="muted">Salidas (outputs)</div>
    <div id="outputs"></div>
  </div>

  <div class="box">
    <div class="muted">Entradas (inputs)</div>
    <div id="inputs"></div>
  </div>

  <div class="box">
    <div class="muted">Diagnóstico</div>
    <div id="diag"></div>
    <div id="err" class="err"></div>
  </div>

<script>
async function apiGet(url){
  const r = await fetch(url);
  return await r.json();
}
async function apiPost(url, body){
  const r = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body || {})
  });
  return await r.json();
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
  const io = await apiGet('/io');
  document.getElementById('backend').textContent = io.backend;
  document.getElementById('diag').textContent = `Uptime: ${io.uptime_seconds}s`;
  document.getElementById('err').textContent = io.error ? io.error : '';
  renderOutputs(io.outputs || []);
  renderInputs(io.inputs || []);
}

async function reloadConfig(){
  await apiPost('/reload', {});
  await refresh();
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
        "config_path": "config/io.yaml",
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
def reload_config():
    io.reload()
    return JSONResponse({"ok": True, "error": io.last_error()})
