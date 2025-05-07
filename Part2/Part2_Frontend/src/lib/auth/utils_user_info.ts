import { userManager } from './userManager';

export default async function getUserInfo() {
    try{
        const user = await userManager.signinRedirectCallback();
        const userInfo = {
        email: user.profile?.email ?? '',
        accessToken: user.access_token,
        idToken: user.id_token,
        refreshToken: user.refresh_token,
        }
        return userInfo;

    } catch (error) {
        console.error('Error fetching user info', error);
    }
}