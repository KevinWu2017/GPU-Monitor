import axios from 'axios'

const request = axios.create({
    // baseURL: 'http://<server-ip>:7030',
    baseURL: 'http://10.0.16.44:7030',
    timeout: 10000,
})
// request 拦截器
request.interceptors.request.use(config => {
    config.headers['Content-Type'] = 'application/json;charset=utf-8';
    return config
}, error => {
    return Promise.reject(error)
});
export default request
