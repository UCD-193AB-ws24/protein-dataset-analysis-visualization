import { UserManager } from 'oidc-client-ts';

export const oidcClient = new UserManager({
	authority: 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_Bep0PJNNp',
	client_id: '6s0tgt4tnp6s02o1j8tmhgqnem',
	redirect_uri: 'https://migrate-amplify.dsu4r7f5bomtn.amplifyapp.com/callback',
	response_type: 'code',
	scope: 'openid email phone'
});
