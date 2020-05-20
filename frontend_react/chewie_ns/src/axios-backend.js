import axios from 'axios';

const instance = axios.create({
   baseURL: 'https://chewbbaca.online/api/NS/api'
});

export default instance;
