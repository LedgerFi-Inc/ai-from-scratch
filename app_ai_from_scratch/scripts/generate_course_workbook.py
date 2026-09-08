#!/usr/bin/env python3
"""Generate the bilingual AIFromScratch visual workbook for PDF and Canva import."""

from __future__ import annotations

import html
import os
import re
from pathlib import Path
from typing import Iterable

from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "output" / "pdf"
CANVA_DIR = ROOT / "output" / "canva"
TMP_DIR = ROOT / "tmp" / "pdfs"
PAGE_W = 960
PAGE_H = 540

NAVY = "#0B1020"
INK = "#162033"
PAPER = "#F8FAFC"
MUTED = "#64748B"
WHITE = "#FFFFFF"
ACCENTS = ["#14B8A6", "#3B82F6", "#8B5CF6", "#EC4899", "#F97316", "#EAB308"]


TOPICS = [
    {
        "title_es": "Aprende viendo ejemplos",
        "title_en": "Learns from examples",
        "objective_es": "Entender cómo los ejemplos etiquetados se convierten en una capacidad para reconocer casos nuevos.",
        "objective_en": "Understand how labelled examples become an ability to recognise new cases.",
        "steps_es": ["Reúne muchos ejemplos", "Etiqueta la respuesta correcta", "Compara y ajusta", "Prueba con casos nuevos"],
        "steps_en": ["Collect many examples", "Label the correct answer", "Compare and adjust", "Test on unseen cases"],
        "mechanism_es": "El modelo intenta una respuesta para cada ejemplo, la compara con la etiqueta y mueve un poco sus números internos. Repite el ciclo hasta que también funciona con ejemplos que nunca vio.",
        "mechanism_en": "For each example, the model makes a guess, compares it with the label and nudges its internal numbers. It repeats until it also works on examples it has never seen.",
        "analogy_es": "Un niño reconoce perros porque muchas personas se los señalan. No memoriza una definición: aprende el parecido al ver casos distintos.",
        "analogy_en": "A child recognises dogs because people point them out many times. They do not memorise a definition; they learn resemblance from varied cases.",
        "example_es": "Entrada: 100.000 fotos marcadas 'gato' o 'perro'.\nSalida: clasifica una foto nueva.\nClave: la prueba final usa fotos que no estaban en el entrenamiento.",
        "example_en": "Input: 100,000 photos labelled 'cat' or 'dog'.\nOutput: classify a new photo.\nKey: the final test uses photos absent from training.",
        "practice_es": "¿Qué datos sirven para distinguir facturas pagadas de pendientes?",
        "practice_en": "Which data can teach a system to distinguish paid from pending invoices?",
        "answer_es": "Muchos ejemplos representativos, cada uno con la etiqueta correcta. Tres facturas sin marcar no bastan.",
        "answer_en": "Many representative examples, each with the correct label. Three unlabelled invoices are not enough.",
    },
    {
        "title_es": "Juega frío y caliente",
        "title_en": "Plays hot and cold",
        "objective_es": "Comprender que entrenar consiste en hacer bajar un número que mide el error.",
        "objective_en": "Understand that training means reducing a number that measures error.",
        "steps_es": ["Intenta responder", "Mide la distancia", "Mueve las perillas", "Vuelve a intentar"],
        "steps_en": ["Make a guess", "Measure the distance", "Move the dials", "Try again"],
        "mechanism_es": "El error indica qué tan lejos quedó la respuesta de la esperada. El entrenamiento busca pequeños cambios que lo reduzcan: 94, luego 23, luego 4.",
        "mechanism_en": "Error measures how far the answer landed from the expected one. Training searches for small changes that reduce it: 94, then 23, then 4.",
        "analogy_es": "Afinas una guitarra: giras una clavija, escuchas y corriges hacia el lado que suena menos mal. El modelo hace algo parecido con muchísimas perillas.",
        "analogy_en": "You tune a guitar by turning a peg, listening, and correcting towards what sounds less wrong. A model does something similar with many dials.",
        "example_es": "Intento 1: 2 + 2 = 7.\nIntento 2: 2 + 2 = 5.\nIntento 3: 2 + 2 = 4.\nEl error mide distancia, no cantidad de aciertos.",
        "example_en": "Attempt 1: 2 + 2 = 7.\nAttempt 2: 2 + 2 = 5.\nAttempt 3: 2 + 2 = 4.\nError measures distance, not a count of correct answers.",
        "practice_es": "El error bajó de 94 a 23. ¿Qué significa?",
        "practice_en": "Error fell from 94 to 23. What does that mean?",
        "answer_es": "La respuesta quedó menos lejos que antes. No significa 23 aciertos ni que ya sea perfecta.",
        "answer_en": "The answer landed closer than before. It does not mean 23 correct answers or that it is already perfect.",
    },
    {
        "title_es": "Todo queda en perillas",
        "title_en": "Everything lives in dials",
        "objective_es": "Ver que lo aprendido queda distribuido en números internos, no en una carpeta de frases o fotos.",
        "objective_en": "See that learning is distributed across internal numbers, not stored in a folder of sentences or photos.",
        "steps_es": ["Entran los datos", "Cambian los números", "Se guarda el modelo", "Los números producen respuestas"],
        "steps_en": ["Data goes in", "Numbers change", "The model is saved", "Numbers produce answers"],
        "mechanism_es": "Cada parámetro es solo un número. Ninguno contiene una idea completa; la capacidad aparece por la combinación de todos. Entrenar cambia su configuración.",
        "mechanism_en": "Each parameter is only a number. No single one contains a complete idea; ability emerges from their combined configuration. Training changes that configuration.",
        "analogy_es": "Una consola de sonido tiene muchas perillas sin una perilla única para 'la voz'. La mezcla correcta depende de cómo quedaron todas juntas.",
        "analogy_en": "A mixing desk has many dials, with no single 'voice' dial. The right mix depends on how all the dials are set together.",
        "example_es": "Al abrir un archivo de modelo ves números como 0.0173, -0.4402 y 1.2088. No aparece un documento que diga 'reglas aprendidas'.",
        "example_en": "Open a model file and you see numbers such as 0.0173, -0.4402 and 1.2088. There is no document called 'learned rules'.",
        "practice_es": "¿Qué ocurre si copias todos los números del modelo a otra máquina compatible?",
        "practice_en": "What happens if you copy all the model's numbers to another compatible machine?",
        "answer_es": "Obtienes la misma configuración del modelo. Puede responder sin repetir todo el entrenamiento.",
        "answer_en": "You get the same model configuration. It can answer without repeating the entire training process.",
    },
    {
        "title_es": "Contigo no aprende",
        "title_en": "It does not learn from your chat",
        "objective_es": "Distinguir entrenamiento, respuesta y memoria de la aplicación.",
        "objective_en": "Distinguish training, answering, and application memory.",
        "steps_es": ["Se entrena", "Las perillas se congelan", "Tú escribes", "Responde sin reentrenarse"],
        "steps_en": ["It is trained", "The dials are frozen", "You type", "It answers without retraining"],
        "mechanism_es": "Hablar con un modelo normalmente usa sus parámetros sin cambiarlos. Una aplicación puede guardar notas o historial y enviarlos otra vez, pero eso no es reentrenar.",
        "mechanism_en": "Talking to a model normally uses its parameters without changing them. An app may save notes or history and send them again, but that is not retraining.",
        "analogy_es": "Un libro ya impreso puede responder muchas consultas. Escribir una nota adhesiva al lado ayuda al lector, pero no reimprime el libro.",
        "analogy_en": "A printed book can support many questions. A sticky note beside it may help the reader, but it does not reprint the book.",
        "example_es": "Hoy dices: 'mi perro se llama Nube'. Mañana solo parece recordarlo si la aplicación guardó ese dato y lo volvió a enviar.",
        "example_en": "Today you say, 'my dog is called Nube'. Tomorrow it only seems to remember if the app stored that detail and sent it again.",
        "practice_es": "Corriges una respuesta hoy. ¿Una conversación nueva lo recordará automáticamente mañana?",
        "practice_en": "You correct an answer today. Will a new chat automatically remember tomorrow?",
        "answer_es": "No. Solo podría aparecer si el producto conserva y reenvía contexto, o si hubo un proceso separado de actualización.",
        "answer_en": "No. It may appear only if the product stores and resends context, or if a separate update process occurred.",
    },
    {
        "title_es": "Lee pedacitos: tokens",
        "title_en": "Reads chunks: tokens",
        "objective_es": "Entender cómo el texto se divide en piezas que el modelo puede procesar.",
        "objective_en": "Understand how text is split into pieces a model can process.",
        "steps_es": ["Recibe texto", "Lo divide en tokens", "Convierte piezas en IDs", "Procesa la secuencia"],
        "steps_en": ["Receive text", "Split it into tokens", "Turn pieces into IDs", "Process the sequence"],
        "mechanism_es": "Un token puede ser una palabra, parte de una palabra o un signo. La división depende del tokenizador y del idioma; no coincide siempre con los espacios.",
        "mechanism_en": "A token may be a word, part of a word, or punctuation. The split depends on the tokenizer and language; it does not always match spaces.",
        "analogy_es": "Son piezas de un rompecabezas de texto. Algunas palabras caben en una pieza; otras necesitan varias piezas que se unen al procesarlas.",
        "analogy_en": "They are pieces of a text puzzle. Some words fit on one piece; others need several pieces that are combined during processing.",
        "example_es": "'gato' puede ocupar 1 token. 'Cartagena' puede dividirse en 2 o más. La división exacta cambia según el modelo.",
        "example_en": "'cat' may take 1 token. 'Cartagena' may split into 2 or more. The exact split changes by model.",
        "practice_es": "¿Por qué tres palabras pueden ocupar cinco tokens?",
        "practice_en": "Why can three words take five tokens?",
        "answer_es": "Porque una o más palabras se dividieron en varias piezas. Los tokens no son un simple conteo de palabras.",
        "answer_en": "Because one or more words were split into several pieces. Tokens are not a simple word count.",
    },
    {
        "title_es": "Elige el siguiente token",
        "title_en": "Chooses the next token",
        "objective_es": "Ver cómo una respuesta aparece una pieza a la vez.",
        "objective_en": "See how an answer appears one piece at a time.",
        "steps_es": ["Mira el contexto", "Calcula probabilidades", "Elige un token", "Lo añade y recalcula"],
        "steps_en": ["Read the context", "Score probabilities", "Choose a token", "Append and recalculate"],
        "mechanism_es": "El modelo no escribe el párrafo completo de una vez. Evalúa opciones para el siguiente token, elige una, la añade y vuelve a calcular con el texto más largo.",
        "mechanism_en": "The model does not write a whole paragraph at once. It scores options for the next token, chooses one, appends it, and recalculates from the longer text.",
        "analogy_es": "Es como el autocompletar del celular, pero con un vocabulario enorme y mucho más contexto disponible para proponer la siguiente pieza.",
        "analogy_en": "It is like phone autocomplete, but with a huge vocabulary and much more context available to propose the next piece.",
        "example_es": "'El café está muy...' -> caliente 31, bueno 22, rico 14, frío 9, resto 24. Elige una opción y vuelve a puntuar.",
        "example_en": "'The coffee is very...' -> hot 31, good 22, nice 14, cold 9, rest 24. It chooses one option and scores again.",
        "practice_es": "¿Por qué el mismo pedido puede producir otra redacción?",
        "practice_en": "Why can the same request produce different wording?",
        "answer_es": "Porque hay varias continuaciones probables y la selección se repite token por token.",
        "answer_en": "Because several continuations may be plausible and selection repeats token by token.",
    },
    {
        "title_es": "La fórmula del buen pedido",
        "title_en": "The good request formula",
        "objective_es": "Convertir una idea vaga en una solicitud que produzca algo usable.",
        "objective_en": "Turn a vague idea into a request that produces something usable.",
        "steps_es": ["Qué necesitas", "Para quién es", "Cómo debe entregarse", "Revisa y ajusta"],
        "steps_en": ["What you need", "Who it is for", "How to deliver it", "Review and refine"],
        "mechanism_es": "Usa un verbo concreto, define la audiencia y especifica formato, tono o límites. Lo que omites suele rellenarse con una opción genérica.",
        "mechanism_en": "Use a concrete verb, define the audience, and specify format, tone, or constraints. What you omit is often filled with a generic choice.",
        "analogy_es": "En un taxi, 'arranque' no basta. Destino, ruta y condición reducen la adivinanza y te acercan al lugar correcto.",
        "analogy_en": "In a taxi, 'drive' is not enough. Destination, route, and conditions reduce guesswork and get you closer to the right place.",
        "example_es": "Vago: 'Escribe algo sobre nuestro producto'.\nMejor: 'Escribe 5 líneas para un cliente actual explicando un aumento del 8 %, con tono claro y respetuoso'.",
        "example_en": "Vague: 'Write something about our product'.\nBetter: 'Write 5 lines for an existing customer explaining an 8% increase, in a clear and respectful tone'.",
        "practice_es": "Mejora: 'Haz una presentación de ventas'.",
        "practice_en": "Improve: 'Make a sales presentation'.",
        "answer_es": "'Crea 6 diapositivas para nuevos clientes, explica problema, solución y precio, con frases breves y una llamada a agendar una demo'.",
        "answer_en": "'Create 6 slides for new customers covering problem, solution, and price, with short sentences and a call to book a demo'.",
    },
    {
        "title_es": "La mesa se llena",
        "title_en": "The desk fills up",
        "objective_es": "Comprender la ventana de contexto y los límites de una conversación larga.",
        "objective_en": "Understand the context window and the limits of a long conversation.",
        "steps_es": ["Entran instrucciones", "Entra tu pedido", "Entran archivos e historial", "Lo antiguo puede quedar fuera"],
        "steps_en": ["Instructions enter", "Your request enters", "Files and history enter", "Older text may fall out"],
        "mechanism_es": "La aplicación envía un bloque limitado de texto al modelo. Cuando no cabe todo, puede resumir, recortar o excluir partes antiguas.",
        "mechanism_en": "The app sends a limited block of text to the model. When everything does not fit, it may summarise, trim, or exclude older material.",
        "analogy_es": "Una mesa solo sostiene cierta cantidad de papeles. Mientras un papel está encima se puede usar; cuando cae al piso deja de estar visible.",
        "analogy_en": "A desk holds only so many papers. While a paper is on top it can be used; after it falls to the floor it is no longer visible.",
        "example_es": "Un nombre puede seguir disponible tres mensajes después, pero perderse en una charla enorme, según cómo la aplicación gestione el contexto.",
        "example_en": "A name may remain available three messages later but disappear in a huge chat, depending on how the app manages context.",
        "practice_es": "¿Qué haces si un detalle antiguo sigue siendo importante?",
        "practice_en": "What should you do if an old detail is still important?",
        "answer_es": "Resúmelo o inclúyelo otra vez de forma clara. No confíes en que todo el historial siga visible.",
        "answer_en": "Summarise it or include it again clearly. Do not assume the entire history remains visible.",
    },
    {
        "title_es": "Seria o creativa: tú eliges",
        "title_en": "Reliable or creative: you choose",
        "objective_es": "Usar la temperatura para controlar variación, sin confundirla con conocimiento.",
        "objective_en": "Use temperature to control variation without confusing it with knowledge.",
        "steps_es": ["Baja: concentra opciones", "Alta: abre opciones", "No añade conocimiento", "Elige según la tarea"],
        "steps_en": ["Low: focus choices", "High: widen choices", "It adds no knowledge", "Match it to the task"],
        "mechanism_es": "Una temperatura baja favorece las opciones más probables. Una más alta deja participar opciones menos probables y aumenta la variedad.",
        "mechanism_en": "A low temperature favours the most likely options. A higher setting gives less likely options more opportunity and increases variety.",
        "analogy_es": "Sin dado, haces la jugada más segura. Con dado, aparecen rutas nuevas: algunas brillantes y otras malas. El tablero no cambia.",
        "analogy_en": "Without dice, you make the safest move. With dice, new paths appear: some brilliant, some poor. The board itself does not change.",
        "example_es": "Baja: datos, resumen, código, traducción.\nMás alta: nombres, lluvia de ideas, escritura creativa.\nSiempre verifica lo importante.",
        "example_en": "Low: facts, summaries, code, translation.\nHigher: names, brainstorming, creative writing.\nAlways verify what matters.",
        "practice_es": "¿Qué conviene para convertir moneda y para proponer nombres de una cafetería?",
        "practice_en": "What suits currency conversion and what suits café name ideas?",
        "answer_es": "Menor variación para la conversión; más variedad para los nombres. La temperatura no hace más cierta una respuesta.",
        "answer_en": "Less variation for conversion; more variety for names. Temperature does not make an answer more factual.",
    },
    {
        "title_es": "Inventa con seguridad",
        "title_en": "Makes things up confidently",
        "objective_es": "Reconocer una respuesta plausible pero falsa y verificar antes de actuar.",
        "objective_en": "Recognise a plausible but false answer and verify before acting.",
        "steps_es": ["Falta información", "Completa un patrón", "Suena convincente", "Verifica la fuente"],
        "steps_en": ["Information is missing", "Complete a pattern", "It sounds convincing", "Verify the source"],
        "mechanism_es": "El modelo busca una continuación probable. Un dato inventado puede tener la forma perfecta aunque no sea verdadero. La fluidez no es evidencia.",
        "mechanism_en": "The model searches for a likely continuation. A made-up fact may have the perfect form even when false. Fluency is not evidence.",
        "analogy_es": "Un amigo servicial da indicaciones seguras en una ciudad que no conoce. Su confianza no reemplaza mirar el mapa.",
        "analogy_en": "A helpful friend gives confident directions in a city they do not know. Their confidence does not replace checking the map.",
        "example_es": "Pides el artículo de una ley. Responde con un número y una cita de aspecto impecable que no existen en la fuente oficial.",
        "example_en": "You ask for a section of law. It answers with a polished-looking number and citation that do not exist in the official source.",
        "practice_es": "¿Cómo pedir un dato legal de forma más segura?",
        "practice_en": "How can you request a legal fact more safely?",
        "answer_es": "Pide qué buscar, fuente oficial, enlace directo y separación entre hechos e incertidumbre. Después abre y verifica la fuente.",
        "answer_en": "Ask what to search, require an official source and direct link, and separate facts from uncertainty. Then open and verify the source.",
    },
    {
        "title_es": "Su conocimiento tiene fecha",
        "title_en": "Its knowledge has a date",
        "objective_es": "Separar lo aprendido durante el entrenamiento de la información recuperada hoy.",
        "objective_en": "Separate what was learned during training from information retrieved today.",
        "steps_es": ["Existe una fecha de corte", "Llega una pregunta reciente", "Busca una fuente actual", "Responde con evidencia"],
        "steps_en": ["There is a cutoff date", "A recent question arrives", "Retrieve a current source", "Answer with evidence"],
        "mechanism_es": "Sin una fuente actual, el modelo puede tratar un dato viejo como si fuera de hoy. Una herramienta de búsqueda puede darle material reciente para responder.",
        "mechanism_en": "Without a current source, the model may present an old fact as current. A search tool can provide recent material for its answer.",
        "analogy_es": "Un enciclopedista en una biblioteca sin ventanas sabe mucho del pasado, pero necesita abrir una ventana para ver qué ocurre hoy.",
        "analogy_en": "An encyclopaedist in a windowless library knows the past well but needs a window to see what is happening today.",
        "example_es": "'¿Cuánto vale el dólar hoy?' Sin búsqueda puede dar un valor viejo. Con búsqueda debe mostrar fecha y enlace de la fuente.",
        "example_en": "'What is the dollar worth today?' Without search it may give an old value. With search it should show a date and source link.",
        "practice_es": "¿Qué evidencia debes pedir para confiar en un dato reciente?",
        "practice_en": "What evidence should you ask for before trusting a recent fact?",
        "answer_es": "Fecha, enlace directo y fuente primaria u oficial. Abre la fuente y comprueba que realmente respalda la afirmación.",
        "answer_en": "A date, direct link, and primary or official source. Open it and confirm that it actually supports the claim.",
    },
    {
        "title_es": "Empieza hoy",
        "title_en": "Start today",
        "objective_es": "Convertir el modelo mental del curso en un hábito breve, útil y seguro.",
        "objective_en": "Turn the course's mental model into a short, useful, and safe habit.",
        "steps_es": ["Elige una tarea real", "Pide qué, para quién y cómo", "Revisa el borrador", "Verifica y decide"],
        "steps_en": ["Choose a real task", "Ask what, who, and how", "Review the draft", "Verify and decide"],
        "mechanism_es": "La IA acelera el primer borrador. Tú aportas objetivo, contexto y criterio; corriges el resultado y verificas cualquier dato con consecuencias.",
        "mechanism_en": "AI accelerates the first draft. You provide goals, context, and judgement; you correct the output and verify any consequential fact.",
        "analogy_es": "Aprendes a conducir con el carro en movimiento y en calles reales. La teoría reduce errores, pero la habilidad llega practicando.",
        "analogy_en": "You learn to drive with the car moving on real streets. Theory reduces mistakes, but skill comes through practice.",
        "example_es": "Tarea real: el correo difícil de hoy. Pide un borrador en 30 segundos, revísalo durante 2 minutos y confirma nombres, cifras y compromisos.",
        "example_en": "Real task: today's difficult email. Ask for a draft in 30 seconds, review for 2 minutes, and confirm names, figures, and commitments.",
        "practice_es": "Plan de 5 minutos: tarea -> pedido -> borrador -> revisión -> verificación. ¿Quién toma la decisión final?",
        "practice_en": "Five-minute plan: task -> request -> draft -> review -> verification. Who makes the final decision?",
        "answer_es": "La persona. La IA acelera y propone; tú decides qué usar, qué corregir y qué comprobar.",
        "answer_en": "The person. AI accelerates and proposes; you decide what to use, correct, and verify.",
    },
]


def color(value: str):
    return HexColor(value)


def wrapped_lines(text: str, font: str, size: float, max_width: float) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if current and stringWidth(trial, font, size) > max_width:
                lines.append(current)
                current = word
            else:
                current = trial
        lines.append(current)
    return lines


def draw_text(c: canvas.Canvas, text: str, x: float, y: float, width: float, *,
              font: str = "Helvetica", size: float = 18, leading: float | None = None,
              fill: str = INK, max_lines: int | None = None) -> float:
    leading = leading or size * 1.28
    lines = wrapped_lines(text, font, size, width)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(".,;:") + "..."
    c.setFont(font, size)
    c.setFillColor(color(fill))
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def rounded(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill: str,
            stroke: str | None = None, radius: float = 18) -> None:
    c.setFillColor(color(fill))
    c.setStrokeColor(color(stroke or fill))
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1 if stroke else 0)


def page_bg(c: canvas.Canvas, accent: str, topic_no: int | None, page_no: int, total_pages: int) -> None:
    c.setFillColor(color(PAPER))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(color(NAVY))
    c.rect(0, PAGE_H - 50, PAGE_W, 50, fill=1, stroke=0)
    c.setFillColor(color(accent))
    c.rect(0, PAGE_H - 54, PAGE_W, 4, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(color(WHITE))
    c.drawString(32, PAGE_H - 31, "AI FROM SCRATCH  /  IA DESDE CERO")
    c.setFont("Helvetica", 10)
    c.drawRightString(PAGE_W - 32, PAGE_H - 31, f"TEMA / TOPIC {topic_no:02d}" if topic_no else "VISUAL WORKBOOK")
    c.setFillColor(color(MUTED))
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W - 28, 18, f"{page_no:02d} / {total_pages:02d}")


def title_block(c: canvas.Canvas, topic: dict, topic_no: int, accent: str, label: str) -> None:
    c.setFillColor(color(accent))
    c.circle(58, 438, 24, fill=1, stroke=0)
    c.setFillColor(color(NAVY))
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(58, 433, str(topic_no))
    c.setFont("Helvetica-Bold", 29)
    c.setFillColor(color(NAVY))
    c.drawString(96, 444, topic["title_es"])
    c.setFont("Helvetica-Bold", 19)
    c.setFillColor(color(MUTED))
    c.drawString(96, 416, topic["title_en"])
    rounded(c, 785, 416, 143, 32, accent)
    c.setFillColor(color(NAVY))
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(856.5, 427, label)


def draw_cover(c: canvas.Canvas) -> None:
    c.setFillColor(color(NAVY))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(color("#111B33"))
    c.circle(830, 470, 210, fill=1, stroke=0)
    c.setFillColor(color("#172554"))
    c.circle(880, 55, 260, fill=1, stroke=0)
    c.setFillColor(color("#5EEAD4"))
    c.setFont("Helvetica-Bold", 15)
    c.drawString(56, 468, "BILINGUAL VISUAL WORKBOOK  /  CUADERNO VISUAL BILINGÜE")
    c.setFillColor(color(WHITE))
    c.setFont("Helvetica-Bold", 48)
    c.drawString(56, 386, "AI From Scratch")
    c.setFont("Helvetica-Bold", 36)
    c.setFillColor(color("#BFDBFE"))
    c.drawString(56, 338, "IA desde cero")
    c.setFont("Helvetica", 19)
    c.setFillColor(color("#CBD5E1"))
    c.drawString(56, 289, "12 visual lessons to understand and use AI")
    c.drawString(56, 261, "12 lecciones visuales para entender y usar la IA")
    for i, topic in enumerate(TOPICS):
        col, row = i % 4, i // 4
        x, y = 56 + col * 214, 177 - row * 55
        accent = ACCENTS[i % len(ACCENTS)]
        rounded(c, x, y, 196, 40, "#16213A", accent, 12)
        c.setFillColor(color(accent))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x + 12, y + 24, f"{i + 1:02d}")
        c.setFillColor(color(WHITE))
        c.setFont("Helvetica-Bold", 10)
        title = topic["title_es"]
        c.drawString(x + 38, y + 24, title[:27] + ("..." if len(title) > 27 else ""))
        c.setFillColor(color("#94A3B8"))
        c.setFont("Helvetica", 8)
        c.drawString(x + 38, y + 10, topic["title_en"][:31])
    c.setFillColor(color("#94A3B8"))
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W - 28, 18, "01 / 49")
    c.showPage()


def draw_intro(c: canvas.Canvas, topic: dict, no: int, page_no: int, total_pages: int, accent: str) -> None:
    page_bg(c, accent, no, page_no, total_pages)
    title_block(c, topic, no, accent, "START / INICIO")
    rounded(c, 32, 292, 438, 96, WHITE, "#E2E8F0")
    c.setFont("Helvetica-Bold", 11); c.setFillColor(color(accent)); c.drawString(52, 366, "OBJETIVO")
    draw_text(c, topic["objective_es"], 52, 343, 394, size=15, max_lines=3)
    rounded(c, 490, 292, 438, 96, WHITE, "#E2E8F0")
    c.setFont("Helvetica-Bold", 11); c.setFillColor(color(accent)); c.drawString(510, 366, "OBJECTIVE")
    draw_text(c, topic["objective_en"], 510, 343, 394, size=15, max_lines=3)
    c.setFillColor(color(NAVY)); c.setFont("Helvetica-Bold", 16); c.drawString(32, 260, "MAPA DEL TEMA  /  TOPIC MAP")
    for i, (es, en) in enumerate(zip(topic["steps_es"], topic["steps_en"])):
        x = 32 + i * 229
        rounded(c, x, 82, 211, 148, WHITE, "#E2E8F0", 16)
        c.setFillColor(color(accent)); c.circle(x + 30, 199, 17, fill=1, stroke=0)
        c.setFillColor(color(NAVY)); c.setFont("Helvetica-Bold", 12); c.drawCentredString(x + 30, 195, str(i + 1))
        draw_text(c, es, x + 18, 166, 175, font="Helvetica-Bold", size=14, max_lines=3)
        c.setStrokeColor(color("#E2E8F0")); c.line(x + 18, 126, x + 193, 126)
        draw_text(c, en, x + 18, 109, 175, size=12, fill=MUTED, max_lines=3)
    c.showPage()


def draw_mechanism(c: canvas.Canvas, topic: dict, no: int, page_no: int, total_pages: int, accent: str) -> None:
    page_bg(c, accent, no, page_no, total_pages)
    title_block(c, topic, no, accent, "HOW / CÓMO")
    c.setFont("Helvetica-Bold", 17); c.setFillColor(color(NAVY)); c.drawString(32, 382, "MECANISMO  /  MECHANISM")
    rounded(c, 32, 214, 438, 142, WHITE, "#E2E8F0")
    c.setFont("Helvetica-Bold", 11); c.setFillColor(color(accent)); c.drawString(52, 332, "ESPAÑOL")
    draw_text(c, topic["mechanism_es"], 52, 303, 394, size=16, leading=21, max_lines=5)
    rounded(c, 490, 214, 438, 142, WHITE, "#E2E8F0")
    c.setFont("Helvetica-Bold", 11); c.setFillColor(color(accent)); c.drawString(510, 332, "ENGLISH")
    draw_text(c, topic["mechanism_en"], 510, 303, 394, size=16, leading=21, max_lines=5)
    for i, (es, en) in enumerate(zip(topic["steps_es"], topic["steps_en"])):
        x = 33 + i * 229
        rounded(c, x, 70, 210, 105, accent if i % 2 == 0 else "#E2E8F0", None, 16)
        c.setFillColor(color(NAVY)); c.setFont("Helvetica-Bold", 17); c.drawString(x + 16, 143, f"0{i + 1}")
        draw_text(c, es, x + 16, 118, 178, font="Helvetica-Bold", size=12, max_lines=2)
        draw_text(c, en, x + 16, 84, 178, size=10, fill=NAVY if i % 2 == 0 else MUTED, max_lines=2)
        if i < 3:
            c.setFillColor(color(NAVY)); c.setFont("Helvetica-Bold", 16); c.drawString(x + 212, 116, ">")
    c.showPage()


def draw_analogy(c: canvas.Canvas, topic: dict, no: int, page_no: int, total_pages: int, accent: str) -> None:
    page_bg(c, accent, no, page_no, total_pages)
    title_block(c, topic, no, accent, "SEE / OBSERVA")
    c.setFont("Helvetica-Bold", 17); c.setFillColor(color(NAVY)); c.drawString(32, 382, "ANALOGÍA COTIDIANA  /  EVERYDAY ANALOGY")
    rounded(c, 32, 238, 896, 118, "#EEF2FF", "#C7D2FE")
    c.setFillColor(color(accent)); c.circle(68, 297, 22, fill=1, stroke=0)
    c.setFillColor(color(NAVY)); c.setFont("Helvetica-Bold", 22); c.drawCentredString(68, 289, "=")
    draw_text(c, topic["analogy_es"], 108, 326, 378, size=15, leading=20, max_lines=5)
    c.setStrokeColor(color("#C7D2FE")); c.line(505, 258, 505, 336)
    draw_text(c, topic["analogy_en"], 530, 326, 370, size=15, leading=20, max_lines=5)
    c.setFont("Helvetica-Bold", 17); c.setFillColor(color(NAVY)); c.drawString(32, 207, "EJEMPLO TRABAJADO  /  WORKED EXAMPLE")
    rounded(c, 32, 62, 438, 122, WHITE, "#E2E8F0")
    c.setFont("Helvetica-Bold", 10); c.setFillColor(color(accent)); c.drawString(52, 160, "ESPAÑOL")
    draw_text(c, topic["example_es"], 52, 137, 394, size=12.5, leading=17, max_lines=6)
    rounded(c, 490, 62, 438, 122, WHITE, "#E2E8F0")
    c.setFont("Helvetica-Bold", 10); c.setFillColor(color(accent)); c.drawString(510, 160, "ENGLISH")
    draw_text(c, topic["example_en"], 510, 137, 394, size=12.5, leading=17, max_lines=6)
    c.showPage()


def draw_practice(c: canvas.Canvas, topic: dict, no: int, page_no: int, total_pages: int, accent: str) -> None:
    page_bg(c, accent, no, page_no, total_pages)
    title_block(c, topic, no, accent, "TRY / PRACTICA")
    rounded(c, 32, 260, 896, 126, NAVY)
    c.setFont("Helvetica-Bold", 12); c.setFillColor(color(accent)); c.drawString(54, 358, "RETO RÁPIDO  /  QUICK CHECK")
    draw_text(c, topic["practice_es"], 54, 329, 405, font="Helvetica-Bold", size=18, leading=23, fill=WHITE, max_lines=4)
    c.setStrokeColor(color("#334155")); c.line(480, 284, 480, 355)
    draw_text(c, topic["practice_en"], 510, 329, 390, font="Helvetica-Bold", size=18, leading=23, fill=WHITE, max_lines=4)
    c.setFont("Helvetica-Bold", 16); c.setFillColor(color(NAVY)); c.drawString(32, 225, "RESPUESTA EXPLICADA  /  EXPLAINED ANSWER")
    rounded(c, 32, 70, 438, 128, "#ECFDF5", "#A7F3D0")
    c.setFillColor(color("#059669")); c.circle(63, 166, 15, fill=1, stroke=0)
    c.setFillColor(color(WHITE)); c.setFont("Helvetica-Bold", 13); c.drawCentredString(63, 161, "OK")
    draw_text(c, topic["answer_es"], 92, 173, 350, size=14, leading=19, max_lines=5)
    rounded(c, 490, 70, 438, 128, "#EFF6FF", "#BFDBFE")
    c.setFillColor(color("#2563EB")); c.circle(521, 166, 15, fill=1, stroke=0)
    c.setFillColor(color(WHITE)); c.setFont("Helvetica-Bold", 13); c.drawCentredString(521, 161, "OK")
    draw_text(c, topic["answer_en"], 550, 173, 350, size=14, leading=19, max_lines=5)
    c.setFont("Helvetica-Bold", 11); c.setFillColor(color(MUTED)); c.drawCentredString(PAGE_W / 2, 43, "La IA acelera; la persona decide.  /  AI accelerates; the person decides.")
    c.showPage()


def build_pdf(path: Path, topic_indexes: Iterable[int] | None = None, include_cover: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    page_no = 1
    if include_cover:
        draw_cover(c)
        page_no += 1
    indexes = list(topic_indexes) if topic_indexes is not None else list(range(len(TOPICS)))
    total_pages = len(indexes) * 4 + (1 if include_cover else 0)
    for idx in indexes:
        topic = TOPICS[idx]
        accent = ACCENTS[idx % len(ACCENTS)]
        no = idx + 1
        draw_intro(c, topic, no, page_no, total_pages, accent); page_no += 1
        draw_mechanism(c, topic, no, page_no, total_pages, accent); page_no += 1
        draw_analogy(c, topic, no, page_no, total_pages, accent); page_no += 1
        draw_practice(c, topic, no, page_no, total_pages, accent); page_no += 1
    c.save()


def html_page(content: str, label: str, accent: str, page_no: int, topic_no: int | None) -> str:
    tag = f"TEMA / TOPIC {topic_no:02d}" if topic_no else "VISUAL WORKBOOK"
    return f'''<section class="page" data-document-role="page" data-label="{html.escape(label)}" style="--accent:{accent}">
      <header><b>AI FROM SCRATCH / IA DESDE CERO</b><span>{tag}</span></header>
      <div class="accent-line"></div>{content}<footer>{page_no:02d} / 49</footer>
    </section>'''


def htext(value: str) -> str:
    return html.escape(value).replace("\n", "<br>")


def build_html(path: Path) -> None:
    pages: list[str] = []
    route = "".join(
        f'<div class="route"><b>{i+1:02d}</b><span>{htext(t["title_es"])}</span><small>{htext(t["title_en"])}</small></div>'
        for i, t in enumerate(TOPICS)
    )
    cover = f'''<div class="cover"><div class="eyebrow">BILINGUAL VISUAL WORKBOOK / CUADERNO VISUAL BILINGÜE</div>
      <h1>AI From Scratch</h1><h2>IA desde cero</h2>
      <p>12 visual lessons to understand and use AI<br>12 lecciones visuales para entender y usar la IA</p>
      <div class="route-grid">{route}</div></div>'''
    pages.append(html_page(cover, "Cover", "#5EEAD4", 1, None))
    page_no = 2
    for idx, topic in enumerate(TOPICS):
        accent = ACCENTS[idx % len(ACCENTS)]
        no = idx + 1
        heading = f'''<div class="title"><span class="num">{no}</span><div><h2>{htext(topic["title_es"])}</h2><h3>{htext(topic["title_en"])}</h3></div></div>'''
        step_cards = "".join(f'<div class="step"><b>{i+1:02d}</b><strong>{htext(es)}</strong><span>{htext(en)}</span></div>' for i,(es,en) in enumerate(zip(topic["steps_es"],topic["steps_en"])))
        intro = heading + f'''<div class="two objectives"><div><label>OBJETIVO</label><p>{htext(topic["objective_es"])}</p></div><div><label>OBJECTIVE</label><p>{htext(topic["objective_en"])}</p></div></div><h4>MAPA DEL TEMA / TOPIC MAP</h4><div class="steps">{step_cards}</div>'''
        pages.append(html_page(intro, f"Topic {no} start", accent, page_no, no)); page_no += 1
        mechanism = heading + f'''<h4>MECANISMO / MECHANISM</h4><div class="two copy"><div><label>ESPAÑOL</label><p>{htext(topic["mechanism_es"])}</p></div><div><label>ENGLISH</label><p>{htext(topic["mechanism_en"])}</p></div></div><div class="flow">{step_cards}</div>'''
        pages.append(html_page(mechanism, f"Topic {no} mechanism", accent, page_no, no)); page_no += 1
        analogy = heading + f'''<h4>ANALOGÍA COTIDIANA / EVERYDAY ANALOGY</h4><div class="two analogy"><div><p>{htext(topic["analogy_es"])}</p></div><div><p>{htext(topic["analogy_en"])}</p></div></div><h4>EJEMPLO TRABAJADO / WORKED EXAMPLE</h4><div class="two copy"><div><label>ESPAÑOL</label><p>{htext(topic["example_es"])}</p></div><div><label>ENGLISH</label><p>{htext(topic["example_en"])}</p></div></div>'''
        pages.append(html_page(analogy, f"Topic {no} example", accent, page_no, no)); page_no += 1
        practice = heading + f'''<div class="challenge"><label>RETO RÁPIDO / QUICK CHECK</label><div class="two bare"><p>{htext(topic["practice_es"])}</p><p>{htext(topic["practice_en"])}</p></div></div><h4>RESPUESTA EXPLICADA / EXPLAINED ANSWER</h4><div class="two answers"><div><b>OK</b><p>{htext(topic["answer_es"])}</p></div><div><b>OK</b><p>{htext(topic["answer_en"])}</p></div></div><div class="closing">La IA acelera; la persona decide. / AI accelerates; the person decides.</div>'''
        pages.append(html_page(practice, f"Topic {no} practice", accent, page_no, no)); page_no += 1

    css = '''
    *{box-sizing:border-box} body{margin:0;background:#dce3ed;font-family:Arial,Helvetica,sans-serif;color:#162033}
    .page{position:relative;width:960px;height:540px;margin:24px auto;background:#F8FAFC;overflow:hidden;page-break-after:always;padding:72px 32px 32px}
    header{position:absolute;left:0;top:0;width:100%;height:50px;background:#0B1020;color:#fff;padding:18px 32px;font-size:11px;letter-spacing:.4px;display:flex;justify-content:space-between}.accent-line{position:absolute;top:50px;left:0;width:100%;height:4px;background:var(--accent)}footer{position:absolute;right:28px;bottom:16px;color:#64748B;font-size:9px}
    .title{height:72px;display:flex;align-items:center;gap:14px}.num{width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--accent);font-size:18px;font-weight:700}.title h2{margin:0;font-size:29px;color:#0B1020}.title h3{margin:3px 0 0;font-size:19px;color:#64748B}.two{display:grid;grid-template-columns:1fr 1fr;gap:20px}.two>div{background:#fff;border:1px solid #E2E8F0;border-radius:16px;padding:18px 20px}label{display:block;color:var(--accent);font-size:11px;font-weight:700;margin-bottom:10px}.two p{margin:0;font-size:16px;line-height:1.35}h4{font-size:16px;margin:18px 0 12px;color:#0B1020}.objectives>div{min-height:94px}.steps,.flow{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}.step{background:#fff;border:1px solid #E2E8F0;border-radius:16px;min-height:136px;padding:18px}.step b{display:block;color:var(--accent);font-size:17px;margin-bottom:16px}.step strong{display:block;font-size:14px;margin-bottom:12px}.step span{display:block;border-top:1px solid #E2E8F0;padding-top:10px;color:#64748B;font-size:12px}.copy>div{min-height:142px}.flow{margin-top:24px}.flow .step{min-height:112px}.analogy>div{background:#EEF2FF;border-color:#C7D2FE;min-height:116px}.challenge{background:#0B1020;color:#fff;border-radius:18px;padding:20px 22px;margin:8px 0 18px}.challenge .bare{gap:32px}.challenge .bare p{font-size:18px;font-weight:700;line-height:1.3}.bare p{padding:0;margin:0}.answers>div{min-height:125px;background:#ECFDF5;border-color:#A7F3D0;display:flex;gap:14px}.answers>div:nth-child(2){background:#EFF6FF;border-color:#BFDBFE}.answers b{width:32px;height:32px;border-radius:50%;background:#059669;color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;flex:none}.answers>div:nth-child(2) b{background:#2563EB}.answers p{font-size:14px}.closing{text-align:center;color:#64748B;font-weight:700;font-size:11px;margin-top:15px}
    .cover{position:absolute;inset:0;background:#0B1020;color:#fff;padding:58px 56px}.cover .eyebrow{color:#5EEAD4;font-size:15px;font-weight:700;margin:0 0 28px}.cover h1{font-size:48px;margin:0}.cover h2{font-size:36px;color:#BFDBFE;margin:3px 0 16px}.cover>p{font-size:19px;line-height:1.5;color:#CBD5E1;margin:0 0 24px}.route-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px 16px}.route{height:48px;border:1px solid #334155;border-radius:12px;background:#16213A;padding:8px 10px;display:grid;grid-template-columns:28px 1fr}.route b{grid-row:1/3;color:#5EEAD4}.route span{font-size:10px;font-weight:700}.route small{color:#94A3B8;font-size:8px}
    @media print{body{background:#fff}.page{margin:0}}
    '''
    document = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>AI From Scratch - Bilingual Visual Workbook</title><style>{css}</style></head><body>{''.join(pages)}</body></html>'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")


def split_topic_htmls(master_path: Path) -> None:
    document = master_path.read_text(encoding="utf-8")
    prefix, body_and_tail = document.split("<body>", 1)
    _, tail = body_and_tail.rsplit("</body>", 1)
    pages = re.findall(r'<section class="page".*?</section>', body_and_tail, flags=re.S)
    if len(pages) != 49:
        raise RuntimeError(f"Expected 49 HTML pages, found {len(pages)}")
    for idx, topic in enumerate(TOPICS):
        selected = pages[1 + idx * 4:1 + (idx + 1) * 4]
        selected = [re.sub(r'<footer>\d{2} / 49</footer>', f'<footer>{page_no:02d} / 04</footer>', page)
                    for page_no, page in enumerate(selected, start=1)]
        slug = f"{idx + 1:02d}_{topic['title_en'].lower().replace(' ', '_').replace(':', '').replace("'", '')}"
        topic_path = CANVA_DIR / f"AIFromScratch_{slug}.html"
        topic_path.write_text(prefix + "<body>" + "".join(selected) + "</body>" + tail, encoding="utf-8")


def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    CANVA_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    build_pdf(PDF_DIR / "AIFromScratch_Bilingual_Visual_Workbook.pdf", include_cover=True)
    for idx, topic in enumerate(TOPICS):
        slug = f"{idx + 1:02d}_{topic['title_en'].lower().replace(' ', '_').replace(':', '').replace("'", '')}"
        build_pdf(PDF_DIR / f"AIFromScratch_{slug}.pdf", [idx])
    master_html = CANVA_DIR / "AIFromScratch_Bilingual_Visual_Workbook.html"
    build_html(master_html)
    split_topic_htmls(master_html)
    print(f"Generated 1 master PDF, {len(TOPICS)} topic PDFs, and {len(TOPICS) + 1} Canva HTML import files.")


if __name__ == "__main__":
    main()
