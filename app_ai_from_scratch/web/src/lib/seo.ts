// JSON-LD y metadatos sociales. Se emiten desde el servidor en cada página
// pública: un crawler que no ejecuta JavaScript los ve igual.
import { SITE, MARCA, AUTOR, ORG, CORREO, PRECIO, MONEDA, LECCIONES, LABS } from './site';
import { seller } from '../data/seller';
import { sameAs } from '../data/social';

export const org = () => ({
  '@type': 'Organization',
  '@id': `${SITE}/#org`,
  name: ORG,
  url: SITE,
  email: CORREO,
  founder: { '@type': 'Person', name: AUTOR },
  address: {
    '@type': 'PostalAddress',
    addressLocality: seller.city,
    addressCountry: seller.country,
    ...(seller.address ? { streetAddress: seller.address } : {}),
  },
  ...(seller.taxId ? { taxID: seller.taxId } : {}),
  ...(seller.phone ? { telephone: seller.phone } : {}),
  ...(sameAs().length ? { sameAs: sameAs() } : {}),
});

export const curso = (idioma: string) => {
  const lang = idioma === 'es' ? 'es' : 'en';
  return ({
  '@type': 'Course',
  '@id': `${SITE}/#curso`,
  name: lang === 'es' ? 'IA desde cero · Fundamentos Vol. 1' : 'AI from scratch · Fundamentals Vol. 1',
  description: lang === 'es'
    ? `Fundamentos de inteligencia artificial para principiantes: ${LECCIONES} lecciones y ${LABS} labs que se resuelven dentro de la lección.`
    : `AI fundamentals for absolute beginners: ${LECCIONES} lessons and ${LABS} labs solved inside the lesson.`,
  inLanguage: [lang, lang === 'es' ? 'en' : 'es'],
  url: `${SITE}/pago`,
  provider: { '@id': `${SITE}/#org` },
  author: { '@type': 'Person', name: AUTOR },
  isAccessibleForFree: false,
  educationalLevel: 'Beginner',
  teaches: lang === 'es'
    ? ['cómo aprende un modelo', 'tokens', 'ventana de contexto', 'temperatura', 'alucinaciones', 'escribir buenos pedidos']
    : ['how a model learns', 'tokens', 'context window', 'temperature', 'hallucinations', 'writing good prompts'],
  offers: {
    '@type': 'Offer', price: PRECIO, priceCurrency: MONEDA, availability: 'https://schema.org/InStock',
    // Monthly access, auto-renewal optional at checkout: not a one-time payment any more.
    url: `${SITE}/pago`, category: 'Subscription',
  },
  hasCourseInstance: {
    '@type': 'CourseInstance', courseMode: 'online', courseWorkload: 'PT5H',
    instructor: { '@type': 'Person', name: AUTOR },
  },
  });
};

type QA = { q: string; a: string };
export const faq = (pares: QA[]) => ({
  '@type': 'FAQPage',
  mainEntity: pares.map(({ q, a }) => ({
    '@type': 'Question', name: q,
    acceptedAnswer: { '@type': 'Answer', text: a },
  })),
});

/** Envuelve los nodos en un solo grafo: un <script> por página, no cinco. */
export const grafo = (...nodos: object[]) => JSON.stringify({ '@context': 'https://schema.org', '@graph': nodos });

export { SITE, MARCA };
