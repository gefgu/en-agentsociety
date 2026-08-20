// // 智能体教育等级
// enum Education {
//     // 未指定
//     EDUCATION_UNSPECIFIED = 0;
//     // 博士
//     EDUCATION_DOCTOR = 1;
//     // 硕士
//     EDUCATION_MASTER = 2;
//     // 本科
//     EDUCATION_BACHELOR = 3;
//     // 高中
//     EDUCATION_HIGH_SCHOOL = 4;
//     // 初中
//     EDUCATION_JUNIOR_HIGH_SCHOOL = 5;
//     // 小学
//     EDUCATION_PRIMARY_SCHOOL = 6;
//     // 大专
//     EDUCATION_COLLEGE = 7;
// }
export const PairEducation = [
    [1, "PhD"],
    [2, "Master's"],
    [3, "Bachelor's"],
    [4, "High School"],
    [5, "Junior High"],
    [6, "Primary School"],
    [7, "Associate's"],
]
export const MapEducation = new Map<number, string>(PairEducation as Iterable<readonly [number, string]>);
export const MapEducationEn = new Map<number, string>([
    [1, "PhD"],
    [2, "Master's"],
    [3, "Bachelor's"],
    [4, "High School"],
    [5, "Junior High"],
    [6, "Primary School"],
    [7, "Associate's"],
]);

// // 智能体性别
// enum Gender {
//     // 未指定
//     GENDER_UNSPECIFIED = 0;
//     // 男性
//     GENDER_MALE = 1;
//     // 女性
//     GENDER_FEMALE = 2;
// }
export const PairGender = [
    [1, "Male"],
    [2, "Female"],
]
export const MapGender = new Map<number, string>(PairGender as Iterable<readonly [number, string]>);
export const MapGenderEn = new Map<number, string>([
    [1, "Male"],
    [2, "Female"],
]);

// // 智能体消费水平
// enum Consumption {
//     // 未指定
//     CONSUMPTION_UNSPECIFIED = 0;
//     // 低
//     CONSUMPTION_LOW = 1;
//     // 较低
//     CONSUMPTION_RELATIVELY_LOW = 2;
//     // 中等
//     CONSUMPTION_MEDIUM = 3;
//     // 较高
//     CONSUMPTION_RELATIVELY_HIGH = 4;
//     // 高
//     CONSUMPTION_HIGH = 5;
// }
export const PairConsumption = [
    [1, "Low"],
    [2, "Below Average"],
    [3, "Average"],
    [4, "Above Average"],
    [5, "High"],
];
export const MapConsumption = new Map<number, string>(PairConsumption as Iterable<readonly [number, string]>);
export const MapConsumptionEn = new Map<number, string>([
    [1, "Low"],
    [2, "Relatively Low"],
    [3, "Medium"],
    [4, "Relatively High"],
    [5, "High"],
]);

export const PairLandUse = [
    [0, 'Unknown'],
    [5, 'Commercial and Service'],
    [6, 'Industrial and Storage'],
    [7, 'Residential'],
    [8, 'Public Administration and Services'],
    [10, 'Transportation'],
    [12, 'Other'],
];
export const MapLandUse = new Map<number, string>(PairLandUse as Iterable<readonly [number, string]>);
export const MapLandUseEn = new Map<number, string>([
    [0, 'Unspecified'],
    [5, 'Commercial'],
    [6, 'Industrial / Warehouse'],
    [7, 'Residential'],
    [8, 'Public / Administrative'],
    [10, 'Transportation'],
    [12, 'Other'],
]);

export const GetEducationName = (education: number, _lang = 'en') => {
    return MapEducationEn.get(education) || 'Unknown';
}

export const GetGenderName = (gender: number, _lang = 'en') => {
    return MapGenderEn.get(gender) || 'Unknown';
}

export const GetConsumptionName = (consumption: number, _lang = 'en') => {
    return MapConsumptionEn.get(consumption) || 'Unknown';
}

export const GetLandUseName = (landUse: number, _lang = 'en') => {
    return MapLandUseEn.get(landUse) || 'Unknown';
}
