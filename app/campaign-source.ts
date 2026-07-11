const PILOT_REQUEST_URL =
  "https://github.com/becastil/Chats-empty-repo/issues/new";
const REFERRAL_OFFER_URL =
  "https://repo-scout.becastil.chatgpt.site/?source=referral#why-teams-buy";

const DISCOVERY_SOURCES = {
  github: "GitHub repository or release",
  website: "Repo Scout website",
  outreach: "Direct outreach",
  referral: "Teammate or referral",
  search: "Search",
  social: "Social media or community",
  other: "Other",
} as const;

type CampaignSource = keyof typeof DISCOVERY_SOURCES;

function normalizeCampaignSource(
  source: string | string[] | undefined,
): CampaignSource {
  const value = Array.isArray(source) ? source[0] : source;
  return value && Object.hasOwn(DISCOVERY_SOURCES, value)
    ? (value as CampaignSource)
    : "website";
}

export function buildPilotRequestUrl(
  source: string | string[] | undefined,
): string {
  const url = new URL(PILOT_REQUEST_URL);
  url.searchParams.set("template", "founding-team-pilot.yml");
  url.searchParams.set(
    "discovery_source",
    DISCOVERY_SOURCES[normalizeCampaignSource(source)],
  );
  return url.toString();
}

export function buildReferralEmailUrl(): string {
  const query = new URLSearchParams({
    subject: "Repo Scout: one repository standard across 10 projects",
    body: [
      "I found Repo Scout, a local open-source repository scanner with a $299 team pilot for applying one policy across up to 10 projects without uploading source code.",
      "",
      "See the team workflow:",
      REFERRAL_OFFER_URL,
    ].join("\n"),
  });
  return `mailto:?${query.toString()}`;
}
