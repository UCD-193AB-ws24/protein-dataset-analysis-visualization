import {
    CognitoUserPool,
    CognitoUser,
    AuthenticationDetails,
    CognitoUserAttribute
  } from 'amazon-cognito-identity-js';
  
  const poolData = {
    UserPoolId: 'us-east-1_Bep0PJNNp',
    ClientId: '6s0tgt4tnp6s02o1j8tmhgqnem'
  };
  
  const userPool = new CognitoUserPool(poolData);
  
  export function signUp(email: string, password: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const attributeList = [new CognitoUserAttribute({ Name: 'email', Value: email })];
  
      userPool.signUp(email, password, attributeList, [], (err, result) => {
        if (err) return reject(err);
        resolve(result);
      });
    });
  }
  
  export function confirmSignUp(email: string, code: string): Promise<any> {
    const user = new CognitoUser({ Username: email, Pool: userPool });
  
    return new Promise((resolve, reject) => {
      user.confirmRegistration(code, true, function (err, result) {
        if (err) return reject(err);
        resolve(result);
      });
    });
  }
  
  
  export function signIn(email: string, password: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const authDetails = new AuthenticationDetails({ Username: email, Password: password });
      const user = new CognitoUser({ Username: email, Pool: userPool });
  
      user.authenticateUser(authDetails, {
        onSuccess: (result) => {
          resolve({
            accessToken: result.getAccessToken().getJwtToken(),
            idToken: result.getIdToken().getJwtToken(),
            refreshToken: result.getRefreshToken().getToken()
          });
        },
        onFailure: (err) => reject(err)
      });
    });
  }
  