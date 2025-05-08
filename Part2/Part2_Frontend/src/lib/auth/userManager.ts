import { UserManager } from "oidc-client-ts";

const cognitoDomain = "https://us-east-1bep0pjnnp.auth.us-east-1.amazoncognito.com";

const cognitoAuthConfig = {
    client_id: "6s0tgt4tnp6s02o1j8tmhgqnem",
    redirect_uri: "https://d37wdymfu5cgqx.cloudfront.net/callback",
    response_type: "code",
    scope: "email openid phone",
    metadata: {
      issuer: cognitoDomain,
      authorization_endpoint: `${cognitoDomain}/oauth2/authorize`,
      token_endpoint: `${cognitoDomain}/oauth2/token`,
      userinfo_endpoint: `${cognitoDomain}/oauth2/userInfo`,
      end_session_endpoint: `${cognitoDomain}/logout`,
      jwks_uri: `https://cognito-idp.us-east-1.amazonaws.com/us-east-1_Bep0PJNNp/.well-known/jwks.json`, // Replace with your actual pool ID
    }
  };

// create a UserManager instance
export const userManager = new UserManager({
    ...cognitoAuthConfig,
});

export async function signOutRedirect () {
    const clientId = "6s0tgt4tnp6s02o1j8tmhgqnem";
    const logoutUri = "https://d37wdymfu5cgqx.cloudfront.net";
    const cognitoDomain = "https://us-east-1bep0pjnnp.auth.us-east-1.amazoncognito.com/";
    await userManager.removeUser();
    window.location.href = `${cognitoDomain}/logout?client_id=${clientId}&logout_uri=${encodeURIComponent(logoutUri)}`;
};