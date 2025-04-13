export const fetchCustom = async (url: string, options: RequestInit = {}) => {
    const response = await fetch(url, options);
    return response;
};
