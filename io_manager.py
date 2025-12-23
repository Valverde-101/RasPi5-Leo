import threading
import time
from pathlib import Path
from typing import Dict, Any

import yaml
from gpiozero import Device


class IOManager:
    def __init__(self, config_path: str = "config/io.yaml"):
        self.config_path = Path(config_path)
        self._lock = threading.Lock()
        self._started_at = time.time()

        self._config: Dict[str, Any] = {}
        self._outputs = {}  # id -> gpiozero device
        self._inputs = {}   # id -> gpiozero device
        self._last_error = None

        self._init_pin_factory()
        self.reload()  # carga config + crea dispositivos

    def _init_pin_factory(self):
        # Pi 5: forzar lgpio chip=0
        from gpiozero.pins.lgpio import LGPIOFactory
        Device.pin_factory = LGPIOFactory(chip=0)

    def uptime_seconds(self) -> int:
        return int(time.time() - self._started_at)

    def last_error(self):
        return self._last_error

    def config(self) -> Dict[str, Any]:
        return self._config

    def reload(self):
        with self._lock:
            self._last_error = None

            # Apaga y cierra lo previo
            for dev in self._outputs.values():
                try:
                    dev.off()
                except Exception:
                    pass
                try:
                    dev.close()
                except Exception:
                    pass

            for dev in self._inputs.values():
                try:
                    dev.close()
                except Exception:
                    pass

            self._outputs.clear()
            self._inputs.clear()

            # Carga YAML
            try:
                data = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
                self._config = data
            except Exception as e:
                self._config = {"outputs": [], "inputs": []}
                self._last_error = f"Config load error: {repr(e)}"
                return

            # Crea outputs/inputs
            try:
                self._create_outputs(self._config.get("outputs", []))
                self._create_inputs(self._config.get("inputs", []))
            except Exception as e:
                self._last_error = f"GPIO init error: {repr(e)}"

    def _create_outputs(self, outputs):
        from gpiozero import LED

        for o in outputs:
            oid = o["id"]
            bcm = int(o["bcm"])
            active_high = bool(o.get("active_high", True))

            # LED en gpiozero permite active_high y estado inicial
            dev = LED(bcm, active_high=active_high, initial_value=False)
            dev.off()  # fail-safe
            self._outputs[oid] = dev

    def _create_inputs(self, inputs):
        from gpiozero import Button

        for i in inputs:
            iid = i["id"]
            bcm = int(i["bcm"])
            pull_up = bool(i.get("pull_up", True))
            # Button para demo (no lo usaremos en UI todavía si no quieres)
            dev = Button(bcm, pull_up=pull_up)
            self._inputs[iid] = dev

    def list_outputs(self):
        outputs_cfg = self._config.get("outputs", [])
        res = []
        for o in outputs_cfg:
            oid = o["id"]
            dev = self._outputs.get(oid)
            is_on = bool(getattr(dev, "is_lit", False)) if dev else False
            res.append({**o, "is_on": is_on})
        return res

    def list_inputs(self):
        inputs_cfg = self._config.get("inputs", [])
        res = []
        for i in inputs_cfg:
            iid = i["id"]
            dev = self._inputs.get(iid)
            # Button: is_pressed
            val = bool(getattr(dev, "is_pressed", False)) if dev else False
            res.append({**i, "value": val})
        return res

    def set_output(self, output_id: str, state: bool) -> bool:
        with self._lock:
            dev = self._outputs.get(output_id)
            if not dev:
                raise KeyError(f"Output not found: {output_id}")

            if state:
                dev.on()
            else:
                dev.off()
            return bool(getattr(dev, "is_lit", False))
