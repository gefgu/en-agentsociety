export const fetchCustom = async (url: string, options: RequestInit = {}) => {
    return fetch(url, options);
};
