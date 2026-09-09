# Railway runbook

```sh
railway whoami --json
railway link --project <project-id> --environment DEV
railway config plan
railway config apply
railway deployment list --environment DEV --json
railway logs --service api --environment DEV --lines 200 --json
```

Use `railway up --ci` only after CI and DEV gates pass. Verify the submitted
deployment reaches `SUCCESS`; queued or exited CLI commands are not success.
For rollback, redeploy the last known-good release, then run
`scripts/health-check.sh` and the smoke suite. Before migrations create a
logical dump and a named Railway backup. Never delete or restore a PROD volume
automatically.
# Incidente Cloudflare 1033: `aifromscratch.shop`

El dominio continúa conectado al túnel Cloudflare nombrado `aifromscratch`.
El error 1033 significa que Cloudflare no tiene ningún `cloudflared` conectado;
no es un fallo de Railway. El origen DEV validado actualmente es
`https://web-dev-a8ad.up.railway.app`, pero no debe usarse para tráfico real.

En el host que sirve el túnel, validar la configuración y arrancarlo:

```bash
cloudflared tunnel ingress validate --config /etc/cloudflared/config.yml
sudo systemctl restart cloudflared
cloudflared tunnel info aifromscratch
```

La configuración de producción debe contener una regla `ingress` para
`aifromscratch.shop` y un origen de PROD real. Si el túnel se mantiene en el
Raspberry Pi, permitir salida TCP y UDP `7844` hacia Cloudflare. No apuntar el
dominio productivo al servicio DEV.
