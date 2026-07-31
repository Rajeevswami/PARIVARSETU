import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { API_BASE_URL } from "@/constants";
import { tokenStorage } from "@/lib/tokenStorage";

export const api = axios.create({baseURL:API_BASE_URL,timeout:15_000,headers:{"Content-Type":"application/json","X-Requested-With":"XMLHttpRequest"}});
api.interceptors.request.use((config)=>{const token=tokenStorage.getAccessToken();if(token)config.headers.Authorization=`Bearer ${token}`;config.headers["X-Request-ID"]=crypto.randomUUID();return config;});
let refreshPromise:Promise<string|null>|null=null;
async function refreshAccessToken(){const refresh=tokenStorage.getRefreshToken();if(!refresh)return null;try{const {data}=await axios.post(`${API_BASE_URL}/auth/token/refresh/`,{refresh},{timeout:15_000});tokenStorage.setAccessToken(data.access);if(data.refresh)tokenStorage.setRefreshToken(data.refresh);return data.access as string;}catch{tokenStorage.clear();return null;}}
const retryable=(error:AxiosError)=>!error.response||[408,429,500,502,503,504].includes(error.response.status);
api.interceptors.response.use(response=>response,async(error:AxiosError)=>{const original=error.config as (InternalAxiosRequestConfig&{_retry?:boolean;_retries?:number})|undefined;if(error.response?.status===401&&original&&!original._retry){original._retry=true;refreshPromise??=refreshAccessToken().finally(()=>{refreshPromise=null;});const access=await refreshPromise;if(access){original.headers.Authorization=`Bearer ${access}`;return api(original);}}
if(original&&retryable(error)&&(original._retries??0)<2){original._retries=(original._retries??0)+1;await new Promise(resolve=>setTimeout(resolve,250*2**original._retries));return api(original);}return Promise.reject(error);});
