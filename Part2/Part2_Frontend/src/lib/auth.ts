import { UserManager } from 'oidc-client-ts';
import { REDIRECT_URI, LOGOUT_URI } from './envs';

export const oidcClient = new UserManager({
	authority: 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_Bep0PJNNp',
	client_id: '6s0tgt4tnp6s02o1j8tmhgqnem',
	redirect_uri: REDIRECT_URI,
	response_type: 'code',
	scope: 'openid email phone'
});

export async function signOutRedirect () {
    const clientId = "6s0tgt4tnp6s02o1j8tmhgqnem";
    const logoutUri = LOGOUT_URI;
    const cognitoDomain = "https://us-east-1bep0pjnnp.auth.us-east-1.amazoncognito.com";
    await oidcClient.removeUser();
    window.location.href = `${cognitoDomain}/logout?client_id=${clientId}&logout_uri=${encodeURIComponent(logoutUri)}`;
};