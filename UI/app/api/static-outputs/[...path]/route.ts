import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

/**
 * 로컬 outputs 폴더의 정적 파일 제공
 * /outputs/cache/{story_id}/{character_id}/page_{page}.wav
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  try {
    // 경로 구성
    const filePath = params.path.join('/');
    
    // 로컬 파일 경로 (service/outputs 폴더)
    const localFilePath = path.join(
      process.cwd(),
      '..',
      'service',
      'outputs',
      filePath
    );

    // 파일 존재 확인
    if (!fs.existsSync(localFilePath)) {
      return new NextResponse('File not found', { status: 404 });
    }

    // 파일 읽기
    const fileBuffer = fs.readFileSync(localFilePath);
    const fileStat = fs.statSync(localFilePath);

    // Content-Type 설정
    const contentType = filePath.endsWith('.wav') 
      ? 'audio/wav' 
      : 'application/octet-stream';

    // 파일 반환
    return new NextResponse(fileBuffer, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Content-Length': fileStat.size.toString(),
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
    });
  } catch (error) {
    console.error('Static file serve error:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}

/**
 * HEAD 요청 처리 (파일 존재 여부 확인용)
 */
export async function HEAD(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  try {
    const filePath = params.path.join('/');
    const localFilePath = path.join(
      process.cwd(),
      '..',
      'service',
      'outputs',
      filePath
    );

    if (!fs.existsSync(localFilePath)) {
      return new NextResponse(null, { status: 404 });
    }

    const fileStat = fs.statSync(localFilePath);
    const contentType = filePath.endsWith('.wav') 
      ? 'audio/wav' 
      : 'application/octet-stream';

    return new NextResponse(null, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Content-Length': fileStat.size.toString(),
      },
    });
  } catch (error) {
    console.error('Static file HEAD error:', error);
    return new NextResponse(null, { status: 500 });
  }
}

