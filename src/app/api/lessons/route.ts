import {NextResponse} from 'next/server';import {scheduleLesson} from '@/server/services';import {prisma} from '@/lib/prisma';
export async function GET(){return NextResponse.json({data:await prisma.lesson.findMany({include:{student:true,instructor:true,vehicle:true},take:50,orderBy:{startsAt:'asc'}})})}
export async function POST(req:Request){try{return NextResponse.json({data:await scheduleLesson(await req.json())},{status:201})}catch(error){return NextResponse.json({error:error instanceof Error?error.message:'Invalid lesson'},{status:422})}}
