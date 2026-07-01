import { UserManager } from 'oidc-client-ts';
import { browser } from '$app/environment';
import { REDIRECT_URI, LOGOUT_URI } from './envs';

// Derive the auth redirect/logout targets from the domain the user is actually
// on (e.g. locuscgv.com vs. the CloudFront URL) so login returns them to the
// same origin instead of a single baked-in domain. Falls back to the build-time
// env values during the non-browser prerender pass, where `window` is undefined.
const redirectUri = browser ? `${window.location.origin}/callback` : REDIRECT_URI;

export const oidcClient = new UserManager({
	authority: 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_Bep0PJNNp',
	client_id: '6s0tgt4tnp6s02o1j8tmhgqnem',
	redirect_uri: redirectUri,
	response_type: 'code',
	scope: 'openid email phone'
});

export async function signOutRedirect () {
    const clientId = "6s0tgt4tnp6s02o1j8tmhgqnem";
    const logoutUri = browser ? window.location.origin : LOGOUT_URI;
    const cognitoDomain = "https://us-east-1bep0pjnnp.auth.us-east-1.amazoncognito.com";
    await oidcClient.removeUser();
    window.location.href = `${cognitoDomain}/logout?client_id=${clientId}&logout_uri=${encodeURIComponent(logoutUri)}`;
};