# Handoff de diseño · Sistema integral de staffing y nómina

**Cotización 2026-017 · Plan Integral · 6.600 USD** — `output/pdf/cotizacion-staffing-integral-usd-6600.pdf`
Stack vendido: TypeScript · Terraform · GCP o AWS. Entrega estimada 40–55 días hábiles. Hosting incluido 12 meses.
Pago 40 % al inicio (2.640) + 60 % al publicar (3.960).

Maquetas navegables del canvas: <https://claude.ai/code/artifact/92723ddd-2148-49aa-a0da-f80dd4a49983>
Este documento es la especificación; el canvas es el píxel.

---

## 1. Qué es

Una empresa de staffing coloca personal en varios clientes. El sistema cubre el ciclo completo:
recibir candidatos → contratarlos → programarles turnos → registrar sus horas → resolver lo que
no cuadra → entregar a nómina un número que alguien revisó y firmó.

**Dos superficies, ambas vendidas:**

| Superficie | Quién la usa | De dónde sale |
|---|---|---|
| Consola web (1440×900) | Coordinación, reclutamiento, gerencia | Esencial 05/09, Profesional 10, Integral 02–08 |
| App nativa iOS/Android (393×852) | Trabajador y supervisor, en sede | **Esencial 12**, heredado vía Profesional 01 → Integral 01 |

La app no es un extra que propongo. Es el punto 12 del Plan Esencial, que el Integral hereda
transitivamente (Integral 01 = «todo el Profesional», Profesional 01 = «todo el Esencial»).

---

## 2. De dónde sale cada pantalla

El Integral son 21 puntos acumulados, no 10. Mapa completo:

| Pantalla | Puntos del alcance que resuelve |
|---|---|
| **Bandeja de excepciones** | Integral 04 · Profesional 03, 04, 05, 06 · Esencial 06 |
| **Conciliación de nómina** | Integral 05 · Profesional 08, 09 · Esencial 07 |
| **Turnos y reglas por sede** | Integral 02, 03 |
| **Candidatos y onboarding** | Integral 06 · Profesional 02 · Esencial 01, 02, 08 |
| **Indicadores y reportes** | Integral 07, 08 · Profesional 07 |
| **App · marcación** | Esencial 04, 12 · Profesional 03, 04 |
| **App · aprobación** | Esencial 12 · Profesional 05, 10 · Integral 04 |

Sin pantalla propia, resueltos dentro de otras o fuera del alcance de diseño:
Esencial 03 (perfil de empleado), 10 (publicación y capacitación), 11 (landing);
Integral 09 (preparación para hardware — es *preparación*, no integración: no dibujes pantalla de dispositivo),
Integral 10 (migración de 500 perfiles — proceso, no interfaz).

---

## 3. Decisiones que hay que cerrar antes de construir

Ninguna de estas está en la cotización. Las cinco cambian el diseño.

1. **¿El cliente final entra a la consola?**
   Integral 02 vende «múltiples clientes». El alcance no dice si Distrialimentos abre sesión para ver
   sus propias horas, o si solo la empresa de staffing opera y le manda reportes.
   *Si entra:* hace falta un rol más, aislamiento por cliente en cada consulta, y un modo de solo lectura.
   *Si no entra:* la consola es interna y los reportes programados (Integral 07) son el único canal.
   **Coste de equivocarse: alto.** Multi-tenant no se añade después sin tocar cada consulta.

2. **¿Qué proveedor de nómina?**
   Profesional 08 dice «un proveedor», singular y sin nombre. El esquema de exportación, el mapeo de
   conceptos (ordinaria / extra / recargo nocturno / dominical) y el manejo de errores dependen de cuál sea.
   Hasta saberlo, la pantalla de conciliación muestra el destino como una fila conectada, sin logo ni campos propios.

3. **¿La app marca sin señal?**
   El alcance **no menciona modo sin conexión**. Bodegas y plantas tienen zonas sin cobertura.
   Si el trabajador no puede marcar, la excepción la resuelve un humano después — que es exactamente
   el trabajo que el sistema promete eliminar.
   Marcación en cola local + sello de hora del dispositivo + reconciliación al recuperar red **no está cotizado**.
   Decidir: se cotiza aparte, o se asume que toda sede tiene cobertura y se documenta.

4. **¿Las reglas laborales cuáles son?**
   Las maquetas usan valores plausibles de Colombia (recargo nocturno desde 21:00, dominical 1,75×,
   extra tras 8 h, tolerancia 10 min, redondeo 5 min). **Me los inventé.** Hay que confirmarlos con el cliente.
   El diseño ya los trata como configurables por sede, así que corregirlos es cambiar datos, no interfaz.

5. **¿Estática o navegable?**
   Lo entregado son maquetas estáticas. Nada responde al clic. Si la venta necesita un prototipo
   navegable, es otro pase de trabajo.

---

## 4. Sistema de diseño

**No es una identidad nueva.** Es la de la propuesta comercial que el cliente ya recibió
(`~/Documents/alpadev/plantillas/propuesta-comercial/Main.dc.html`). El objetivo es que el documento
y el producto se lean como una sola cosa.

### Color

Los tokens originales están en `oklch`. El hex es equivalente aproximado, para Figma o iOS.

| Token | Valor | ~Hex | Uso |
|---|---|---|---|
| `papel` | `oklch(0.995 0.002 265)` | `#FDFDFF` | Fondo de toda la aplicación |
| `panel` | `oklch(0.975 0.004 265)` | `#F5F7FA` | Barra lateral, barra de pestañas |
| `tinta` | `oklch(0.22 0.012 265)` | `#181B20` | Texto principal |
| `apagado` | `oklch(0.45 0.012 265)` | `#52555C` | Texto secundario |
| `tenue` | `oklch(0.62 0.010 265)` | `#83868C` | Etiquetas, marcas de agua |
| `línea` | `oklch(0.90 0.006 265)` | `#DCDEE2` | **Todos** los separadores, 1 px |
| `acento` | — | `#22448F` | Marca, selección, acción primaria |
| `bien` | — | `#2F5D4A` | Conciliado, dentro de regla, aprobado |
| `atención` | — | `#7A3B2E` | Excepción, faltante, bloqueo |

Verde y terracota **ya venían en la plantilla** como opciones alternas de acento
(`data-props: options: ["#22448f","#1a1a1a","#2f5d4a","#7a3b2e"]`). Aquí ascienden a semánticos.
No hay ámbar: tres colores bastan y más ensucia.

Lavados: selección `rgba(34,68,143,.055–.07)` · fila con excepción `rgba(122,59,46,.045)` ·
celda de turno cubierto `rgba(34,68,143,.06)`.

### Tipografía

**Archivo** (Google Fonts), pesos 400 / 500 / 600 solamente. Sin 700 — el peso alto es lo que
abarata el conjunto. Respaldo: `'Helvetica Neue', Arial, sans-serif`.

| Rol | Consola | App |
|---|---|---|
| Cifra grande | 30–32 px / 500 / `-.8…-.9 px` | 54 px / 500 / `-2.2 px` (reloj) |
| Título de pantalla | 19 px / 600 / `-.2 px` | 24–26 px / 500 / `-.7 px` |
| Título de panel | 21–22 px / 500 / `-.4 px` | — |
| Cuerpo | 13–14 px / 400 | 15 px / 400 |
| Dato de tabla | 13–13,5 px / 400–500 | 14 px |
| Microetiqueta | 10 px / 600 / `+1.5 px` / MAYÚSCULAS / `tenue` | igual |

**Todo número lleva `font-variant-numeric: tabular-nums`.** Sin excepción. Es lo que permite comparar
una columna de horas de un vistazo, y es la mitad de por qué esto se ve caro.

### Forma y espacio

- **Radio 0 en todo, salvo controles interactivos: 3 px.** Botones, campos, avatares. Nada más.
- **Cero sombras. Cero degradados. Cero cajas de relleno.** La jerarquía la hace la línea de 1 px
  y el espacio en blanco. Es la regla del documento y es lo que hay que defender cuando alguien
  pida «darle vida».
- Rejilla vertical de 4 px. Alturas: fila de tabla 66 px (bandeja) / 54 px (conciliación);
  control 34 px en consola, 44–52 px en app; barra superior 68 px; barra lateral 232 px.
- Márgenes: consola 32 px horizontal; app 22 px.
- Acento estructural: barra izquierda de **2 px** en el elemento seleccionado o en bloque de énfasis.
  Nunca un borde completo de color.

---

## 5. Componentes

| Componente | Especificación |
|---|---|
| **Barra lateral** | 232 px, fondo `panel`, borde derecho 1 px. Cabecera 68 px alineada con la barra superior. Ítem 34 px, activo = fondo `rgba(34,68,143,.07)` + texto acento + peso 600. Contadores a la derecha en `tabular-nums`. |
| **Barra superior** | 68 px, borde inferior 1 px. Título 19/600 + subtítulo 12,5 con periodo. Acciones a la derecha: secundaria(s) y luego una sola primaria. |
| **Fila de tabla** | Borde **superior** de 1 px (no inferior, no cebra). Sin fondo salvo estado. Fila total con borde superior `tinta` en lugar de `línea`. |
| **Cabecera de tabla** | 32–34 px, microetiquetas, sin fondo, sin borde. |
| **Filtro (chip)** | 30 px, borde 1 px, radio 3 px. Activo = borde y texto acento + lavado. Punto de 5 px cuando el filtro tiene color semántico. |
| **Botón** | Primario: fondo acento, texto blanco, 600. Secundario: borde `línea`, texto `tinta`, fondo transparente. Deshabilitado: `opacity: .42` (no se cambia el color). |
| **Panel de detalle** | 340–380 px, borde izquierdo 1 px, tres zonas: cabecera fija, cuerpo, pie fijo con acciones. |
| **Par clave-valor** | `justify-content: space-between`, borde superior 1 px, clave en `apagado`, valor en 500. |
| **Bloque de énfasis** | Barra izquierda 2 px del color semántico + 14 px de sangría. Sustituye a la tarjeta de alerta. |
| **Barra de progreso** | Segmentos de 3 px separados 2–3 px, no una barra continua. Llenos en acento, vacíos en `línea`. |
| **Iconos** | Trazo de 1,6–1,8 px, `stroke-linecap: round`. 16 px en barra lateral, 14–17 px en línea, 22 px en pestañas. |

---

## 6. Las siete pantallas

### 6.1 Bandeja de excepciones — pantalla del día a día

La primera que se abre cada mañana. Todo lo que no cuadró, de todos los clientes, en una lista.

- **Filtros:** Todas · Faltantes · Tardanzas · Horas extra · Fuera de sede. Con contadores.
- **Columnas:** selección · Empleado (nombre + cédula enmascarada + cargo) · Cliente · Sede ·
  Turno · Marcación (`entrada → salida`) · Diferencia (derecha, 600, color semántico) · Motivo.
- **Selección múltiple** para resolución en lote; el botón primario dice cuántas van.
- **Panel de detalle:** turno y regla aplicada → marcación con método (PIN o QR) → evidencia
  (geocerca con distancia real, dispositivo registrado, foto si la sede la exige) → diferencia
  en grande con la consecuencia escrita en prosa → nota para nómina → dos acciones.

**Estados de fila:** excepción abierta (terracota) · pendiente de aprobar (acento) ·
resuelta por regla automática (verde, sin acción) · sin marcación (valor `—`).

**La línea que importa,** en el pie del panel: *«Queda registrado en auditoría con tu usuario, la hora
y el valor anterior.»* Eso es Integral 08 hecho visible en el momento en que alguien toca un número.

### 6.2 Conciliación previa a nómina — donde se vende el plan

- Cuatro cifras del periodo: empleados · horas ordinarias · extras y recargos · valor estimado en COP.
- **Bloqueo explícito:** con discrepancias abiertas, el botón de cerrar va al 42 % de opacidad y
  un bloque en terracota dice por qué. *El periodo no se exporta hasta que alguien resolvió todo.*
  Esa frase es el argumento comercial entero del Plan Integral; no la suavices.
- Tabla por **cliente × centro de costo** con fila de total (borde superior `tinta`).
- **Destino al cerrar:** proveedor de nómina conectado + respaldo estructurado CSV/JSON con retención.
- **Historial:** periodos cerrados con quién, cuándo, cuánto y enlace al respaldo. Un periodo
  muestra «reabierto una vez» — el caso incómodo tiene que ser visible, no esconderse.

### 6.3 Turnos y reglas por sede

- **Árbol cliente → sede** a la izquierda (200 px). Es la prueba visual de Integral 02.
- **Rejilla semanal:** 3 turnos × 7 días. Celda = `cubiertos/requeridos` + barra inferior de 3 px.
  Falta de personal en terracota con «Falta N». Domingo marcado `1,75×`. Turno inexistente = borde
  punteado, «Sin turno». Fila de horas por día al pie.
- **Panel de reglas** (300 px): tolerancia, redondeo, descanso, umbral de extra, inicio de recargo
  nocturno, factor dominical, radio de geocerca, métodos de marcación, evidencia obligatoria, foto.
  Cierra con: *«Estas reglas solo aplican aquí. Las otras 10 sedes tienen las suyas y ninguna se pisa.»*
  Eso es Integral 03 dicho en una frase.

### 6.4 Candidatos y onboarding

- Tablero de 4 columnas: **Solicitud · Preselección · Documentos · Contratación**.
  «Activo» no es columna: es post-contratación, vive en la ficha del empleado.
- La tarjeta lleva el estado del **seguimiento automático** (Integral 06): «Recordatorio hace 2 d»,
  «Sin respuesta · 3.er aviso» en terracota, «Vencido · 5 d sin subir».
- Columna Documentos: barra segmentada `4 de 6`.
- **Panel de onboarding:** checklist de 6 documentos con fecha de recepción, y la línea de tiempo de
  avisos enviados incluido el próximo programado.
- Nota obligatoria: *«Los correos llevan solo un enlace con caducidad. Nunca adjuntan documentos ni
  datos sensibles.»* — Esencial 08. No es decoración legal, es un requisito del alcance.

### 6.5 Indicadores y reportes

- Cuatro indicadores con variación contra el periodo anterior. **El color sigue al negocio, no al signo:**
  «horas extra 7,1 % ▼» va en verde porque bajar es bueno; «días para contratar 6,2 ▲» va en terracota.
- Barras de excepciones por semana con tendencia a la baja — las dos últimas en acento sólido.
- Desglose por motivo, cuyos números **cuadran con la bandeja** (5 + 4 + 3 + 2 = 14).
- **Reportes programados** (Integral 07): reporte · destinatarios · frecuencia · próximo envío · formato.
- **Auditoría** (Integral 08): últimos movimientos con usuario, hora y qué cambió. Incluye acciones del
  sistema y una reapertura de periodo. Pie: retención 24 meses, solo lectura.

### 6.6 App · marcación (trabajador)

- Reloj de 54 px, turno del día, y una línea de estado que dice **qué va a pasar**:
  «Tu turno empieza en 2 minutos» + «Estás dentro de la sede, a 40 m del punto».
- Acción primaria de 50 px: **Marcar entrada**. Debajo, los dos métodos como acciones secundarias
  de 42 px: **Código QR** y **PIN** (Profesional 03).
- «Tu día»: entrada prevista, descanso, salida prevista, tolerancia. El trabajador ve la regla que
  lo va a juzgar **antes** de que lo juzgue.
- «Esta semana»: 32:00 de 48:00 en barra segmentada.
- Pestañas: Turno · Horas · Documentos · Perfil.

### 6.7 App · aprobación (supervisor)

- Tres cifras: marcaciones · sin novedad · con novedad.
- **Acción en lote primero:** «Aprobar las 15 sin novedad». El supervisor no debería tocar 18 tarjetas
  para atender 3 problemas.
- Las 3 con novedad: la primera abierta con evidencia y dos acciones (Aprobar N / Ajustar);
  las otras dos colapsadas en una línea con la diferencia y el motivo.
- Pie: *«Lo que apruebes entra a la conciliación del periodo con tu nombre y la hora.»*
- Pestañas: Turnos · **Por aprobar (3)** · Equipo · Perfil. La insignia va en terracota.

---

## 7. Reglas de negocio que el diseño asume

Valores **inventados** para las maquetas. Confírmalos con el cliente; la interfaz ya los trata como
configurables por sede, así que corregirlos no cuesta rediseño.

| Regla | Valor en las maquetas | Dónde se ve |
|---|---|---|
| Tolerancia de entrada | 10 min | Turnos, Bandeja, App marcación |
| Redondeo de marcación | 5 min | Turnos, Bandeja |
| Descanso no pagado | 60 min | Turnos, App marcación |
| Umbral de hora extra | tras 8 h | Turnos |
| Inicio de recargo nocturno | 21:00 | Turnos |
| Factor dominical y festivo | 1,75× | Turnos |
| Radio de geocerca | 150 m | Turnos, Bandeja, App |
| Métodos de marcación | PIN y QR | Turnos, App |
| Retención de auditoría | 24 meses | Indicadores, Conciliación |

Las cédulas van **siempre enmascaradas** en listas (`CC 1.017·•••`). El nombre completo basta para
identificar; el documento completo solo en la ficha, y con permiso.

---

## 8. Datos de las maquetas

Ficticios y **consistentes entre pantallas**, a propósito: cuando enseñes esto en una reunión y
alguien cruce dos pantallas, los números tienen que cuadrar.

- 5 clientes, 11 sedes — coincide con el contador de la barra lateral.
- 312 empleados en el periodo = suma exacta de las 6 filas de la conciliación.
- 41.860 h ordinarias, 3.214 extras, 2.300 de recargo nocturno = sumas exactas de sus columnas.
- 14 excepciones abiertas = insignia de la barra lateral = total del desglose por motivo.
- 3 discrepancias sin resolver = las que bloquean el cierre = las 3 de la app del supervisor.

Las empresas son inventadas (Distrialimentos, Clínica Santa Rosa, Puerto Verde, Textiles Andes,
Logística Caribe). **No uses nombres de empresas reales en una maqueta comercial.**

---

## 9. Lo que no verifiqué

- **Las reglas laborales colombianas.** No confirmé el recargo nocturno, el factor dominical ni el
  umbral de extra contra la normativa vigente. Son plausibles, no auditados.
- **El cálculo del valor del periodo.** $ 318.204.900 COP para 312 personas en quincena es un orden
  de magnitud razonable, no una tarifa real.
- **La cabida en pantallas menores.** Las maquetas son 1440×900 y 393×852 exactos, medidos sin recorte.
  No probé 1280 de ancho, ni iPhone SE, ni tableta. Esencial 09 vende adaptable: hace falta ese pase.
- **Accesibilidad.** No medí contraste. El texto `tenue` (`#83868C`) sobre `papel` está cerca del
  límite de AA para 10 px; verificar antes de construir.
- **Nada de esto está conectado a código.** No hay repositorio de este producto todavía.

---

*Alejandro Padrón · 28 · 08 · 2026*
