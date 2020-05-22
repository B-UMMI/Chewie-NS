import axios from 'axios';

const instance = axios.create({
   baseURL: 'https://194.210.120.209/api/NS/api',
   headers: { 'Content-Type': 'application/json' },
});

export default instance;
