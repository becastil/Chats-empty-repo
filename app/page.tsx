import {
  buildPilotRequestUrl,
  buildReferralEmailUrl,
} from "./campaign-source";
import RepoScoutPage from "./repo-scout-page";

type HomeProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function Home({ searchParams }: HomeProps) {
  const params = await searchParams;
  return (
    <RepoScoutPage
      pilotRequestUrl={buildPilotRequestUrl(params.source)}
      referralEmailUrl={buildReferralEmailUrl()}
    />
  );
}
