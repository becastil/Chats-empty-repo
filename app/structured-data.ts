import {
  PORTABLE_RELEASE_URL,
  RELEASE_VERSION,
  SITE_DESCRIPTION,
  SITE_URL,
} from "./site-config";

export const STRUCTURED_DATA = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "SoftwareApplication",
      "@id": `${SITE_URL}/#software`,
      name: "Repo Scout",
      description: SITE_DESCRIPTION,
      url: `${SITE_URL}/`,
      applicationCategory: "DeveloperApplication",
      operatingSystem: "Any system with Python 3.11 or newer",
      softwareVersion: RELEASE_VERSION,
      downloadUrl: PORTABLE_RELEASE_URL,
      license:
        "https://github.com/becastil/Chats-empty-repo/blob/main/LICENSE",
      featureList: [
        "Local repository snapshots",
        "Version-controlled repository policies",
        "CI policy enforcement",
        "Cross-repository rollout evidence",
      ],
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "USD",
        availability: "https://schema.org/InStock",
        url: PORTABLE_RELEASE_URL,
      },
    },
    {
      "@type": "Service",
      "@id": `${SITE_URL}/#team-pilot`,
      name: "Repo Scout Founding Team Pilot",
      description:
        "A 90-day repository policy and CI rollout pilot for up to 10 software projects without uploading source code.",
      serviceType: "Repository policy and CI rollout support",
      url: `${SITE_URL}/#team-pilot`,
      audience: {
        "@type": "BusinessAudience",
        audienceType:
          "Software teams with 5 to 50 developers using coding agents across multiple repositories",
      },
      offers: {
        "@type": "Offer",
        price: "299",
        priceCurrency: "USD",
        availability: "https://schema.org/LimitedAvailability",
        url: `${SITE_URL}/#team-pilot`,
      },
    },
  ],
} as const;

export function serializeStructuredData(): string {
  return JSON.stringify(STRUCTURED_DATA).replaceAll("<", "\\u003c");
}
