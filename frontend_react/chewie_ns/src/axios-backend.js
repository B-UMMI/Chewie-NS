import axios from 'axios';

//const spdy = require('spdy');
//const https = require('https');

const instance = axios.create({
   baseURL: 'https://192.210.120.209/api/NS/api'
   //adapter: require('axios/lib/adapters/http')
   //httpsAgent: new https.Agent({ keepAlive: true, rejectUnauthorized: false })
   //httpsAgent: new spdy.createAgent(sslOptions),
   //withCredentials: true
   //baseURL: 'http://172.19.1.1:5000/NS/api'
   //baseURL: 'http://127.0.0.1:5000/NS/api/'
});

export default instance;
