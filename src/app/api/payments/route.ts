import {NextResponse} from 'next/server';import {recordPayment} from '@/server/services';
export async function POST(req:Request){const {studentId,invoiceId,amount,method}=await req.json();return NextResponse.json({data:await recordPayment(studentId,invoiceId,Number(amount),method)},{status:201})}
