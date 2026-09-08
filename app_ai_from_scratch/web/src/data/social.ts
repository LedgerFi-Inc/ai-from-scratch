const env = (k: string): string => String(import.meta.env[k] ?? process.env[k] ?? '').trim();

export const social = {
  facebook: env('PUBLIC_SOCIAL_FACEBOOK'),
  instagram: env('PUBLIC_SOCIAL_INSTAGRAM'),
  youtube: env('PUBLIC_SOCIAL_YOUTUBE'),
  youtubeId: env('PUBLIC_YOUTUBE_ID'),
};

export const socialLinks = (): { label: string; href: string }[] => {
  const out: { label: string; href: string }[] = [];
  if (social.facebook) out.push({ label: 'Facebook', href: social.facebook });
  if (social.instagram) out.push({ label: 'Instagram', href: social.instagram });
  if (social.youtube) out.push({ label: 'YouTube', href: social.youtube });
  return out;
};

export const sameAs = (): string[] => socialLinks().map((x) => x.href);
