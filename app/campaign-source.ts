const PILOT_REQUEST_URL =
  "https://github.com/becastil/Chats-empty-repo/issues/new";

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
