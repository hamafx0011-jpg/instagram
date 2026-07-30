import {z} from 'zod';
export const permissions=['view_students','create_students','edit_students','delete_students','manage_instructors','manage_vehicles','manage_lessons','manage_payments','manage_packages','manage_exams','view_reports','manage_users','manage_settings','view_gps','manage_gps','manage_notifications'] as const;
export type PermissionKey=typeof permissions[number];
export const rolePermissions:Record<string,PermissionKey[]>={
'Super Admin':[...permissions],'Office Admin':permissions.filter(p=>p!=='delete_students'),'Receptionist':['view_students','create_students','edit_students','manage_lessons','manage_notifications'],'Instructor':['view_students','manage_lessons','view_gps','manage_gps'],'Accountant':['view_students','manage_payments','view_reports'],'Student':[],'Manager':['view_students','manage_instructors','manage_vehicles','manage_lessons','view_reports','view_gps']};
export const studentSchema=z.object({fullName:z.string().min(2),phone:z.string().min(7),email:z.string().email().optional().or(z.literal('')),licenseCategory:z.string().min(1),nationalId:z.string().optional(),address:z.string().optional()});
export const lessonSchema=z.object({studentId:z.string(),instructorId:z.string(),vehicleId:z.string().optional(),startsAt:z.coerce.date(),endsAt:z.coerce.date(),location:z.string().min(2),type:z.enum(['THEORY','PRACTICAL','EXAMINATION'])}).refine(v=>v.endsAt>v.startsAt,{message:'End time must be after start time'});
export function overlaps(aStart:Date,aEnd:Date,bStart:Date,bEnd:Date){return aStart<bEnd&&bStart<aEnd}
export function calculateInvoice(total:number,discount=0,tax=0,paid=0){const finalTotal=Math.max(0,total-discount+tax);return{total,discount,tax,finalTotal,remaining:Math.max(0,finalTotal-paid),paidAmount:paid}}
export function evaluationAverage(scores:Record<string,number>){const vals=Object.values(scores);if(!vals.length)return 0;return Math.round(vals.reduce((a,b)=>a+b,0)/vals.length*100)/100}
