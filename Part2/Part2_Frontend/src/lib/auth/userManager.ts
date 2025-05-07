import { UserManager } from "oidc-client-ts";

const cognitoAuthConfig = {
    authority: "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_Bep0PJNNp",
    client_id: "6s0tgt4tnp6s02o1j8tmhgqnem",
    redirect_uri: "http://localhost:5173/callback",
    response_type: "code",
    scope: "email openid phone"
};

// create a UserManager instance
export const userManager = new UserManager({
    ...cognitoAuthConfig,
});

export async function signOutRedirect () {
    const clientId = "6s0tgt4tnp6s02o1j8tmhgqnem";
    const logoutUri = "http://localhost:5173";
    const cognitoDomain = "https://us-east-1bep0pjnnp.auth.us-east-1.amazoncognito.com";
    await userManager.removeUser();
    window.location.href = `${cognitoDomain}/logout?client_id=${clientId}&logout_uri=${encodeURIComponent(logoutUri)}`;
};