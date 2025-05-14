import { oidcClient } from '$lib/auth';

export async function getTokens() {
  const user = await oidcClient.getUser();
  return {
    idToken: user?.id_token ?? '',
    accessToken: user?.access_token ?? '',
  };
}
