# Tallo UI

페르소나 기반 인터랙티브 동화 서비스의 프론트엔드 애플리케이션입니다.

## 🛠 기술 스택

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Fonts**: Noto Sans KR (Google Fonts)

## 📁 프로젝트 구조

```
UI/
├── app/                      # Next.js App Router
│   ├── layout.tsx           # 루트 레이아웃
│   ├── page.tsx             # 메인 페이지
│   └── globals.css          # 글로벌 CSS
├── components/              # React 컴포넌트
│   ├── CharacterCard.tsx
│   ├── CharacterSelector.tsx
│   ├── CharacterViewer.tsx
│   ├── ChatPanel.tsx
│   ├── ChoiceButtons.tsx
│   └── StoryBookPanel.tsx
├── data/                    # 더미 데이터 (백엔드 연동 전)
│   ├── characters.ts
│   └── storyPages.ts
├── lib/                     # 유틸리티 & 서비스
│   ├── api.ts              # API 클라이언트
│   ├── store.ts            # Zustand 상태 관리
│   └── utils.ts            # 헬퍼 함수
├── types/                   # TypeScript 타입 정의
│   └── index.ts
├── public/                  # 정적 파일
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

## 🚀 시작하기

### 1. 의존성 설치

```powershell
# UI 디렉토리로 이동
cd UI

# npm 사용
npm install

# 또는 yarn 사용
yarn install

# 또는 pnpm 사용 (권장)
pnpm install
```

### 2. 환경 변수 설정

`.env.local` 파일을 생성하고 아래 내용을 추가하세요:

```env
# 백엔드 API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. 개발 서버 실행

```powershell
npm run dev
# 또는
yarn dev
# 또는
pnpm dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 확인하세요.

### 4. 빌드 (프로덕션)

```powershell
npm run build
npm run start
```

## 📝 주요 컴포넌트 설명

### `app/page.tsx` - 메인 페이지
- 전체 레이아웃을 구성하는 최상위 페이지
- 좌측(캐릭터/채팅), 중앙(캐릭터 뷰어), 우측(동화책) 3단 구조
- 상태 관리 및 이벤트 핸들링

### `components/CharacterSelector.tsx`
- 캐릭터 선택 그리드 뷰
- TODO: 백엔드 API에서 사용자의 캐릭터 목록 가져오기

### `components/ChatPanel.tsx`
- 캐릭터와의 대화 인터페이스
- 메시지 목록 표시 및 자동 스크롤

### `components/CharacterViewer.tsx`
- 중앙의 캐릭터 표시 영역
- TODO: Three.js로 3D 캐릭터 렌더링
- TODO: 립싱크 애니메이션 적용

### `components/StoryBookPanel.tsx`
- 동화책 형식의 스토리 표시
- 페이지 네비게이션 및 진행 표시

### `components/ChoiceButtons.tsx`
- 인터랙티브 선택지 버튼
- 사용자 선택에 따라 스토리 분기

### `lib/store.ts` - 상태 관리 (Zustand)
- 전역 상태 관리
- 캐릭터, 메시지, 재생 상태 등

### `lib/api.ts` - API 클라이언트
- 백엔드 FastAPI 서버와 통신
- **현재는 더미 데이터 반환 (TODO 주석 참조)**

## 🔧 백엔드 API 연동 방법

현재 프론트엔드는 더미 데이터로 동작합니다. 백엔드 연동 시 아래 파일들을 수정하세요:

### 1. `lib/api.ts`
각 함수의 `TODO` 주석을 참고하여 실제 API 호출로 변경:

```typescript
// 현재 (더미)
export async function fetchCharacters() {
  console.warn('[API] 더미 데이터 사용 중');
  return Promise.resolve([]);
}

// 변경 후 (실제 API)
export async function fetchCharacters() {
  const response = await apiClient.get('/api/characters');
  return response.data;
}
```

### 2. `components/CharacterSelector.tsx`
React Query를 사용하여 데이터 페칭:

```typescript
import { useQuery } from '@tanstack/react-query';
import { fetchCharacters } from '@/lib/api';

const { data: characters, isLoading, error } = useQuery({
  queryKey: ['characters'],
  queryFn: fetchCharacters
});
```

### 3. WebSocket 연동 (실시간 인터랙티브)
`lib/api.ts`의 `createStoryWebSocket` 함수 주석 해제

### 4. 환경변수 설정
`.env.local` 파일에 실제 백엔드 URL 설정

## 📦 추가 패키지 설치 (필요 시)

### Three.js (3D 캐릭터 렌더링)
```powershell
npm install three @react-three/fiber @react-three/drei
npm install -D @types/three
```

### React Query (데이터 페칭)
```powershell
npm install @tanstack/react-query
```

### Audio 관련
```powershell
npm install howler
npm install -D @types/howler
```

## 🎨 스타일 커스터마이징

### Tailwind CSS
`tailwind.config.js`에서 테마 수정:
```javascript
theme: {
  extend: {
    colors: {
      // 커스텀 컬러 추가
    },
    animation: {
      // 커스텀 애니메이션 추가
    }
  }
}
```

### 글로벌 CSS
`app/globals.css`에서 커스텀 스타일 추가

## 🐛 문제 해결

### 타입 에러
패키지 설치 후에도 타입 에러가 나는 경우:
```powershell
npm install -D @types/node @types/react @types/react-dom
```

### 빌드 에러
캐시 삭제 후 재시도:
```powershell
rm -rf .next
npm run build
```

### API 연결 실패
1. 백엔드 서버가 실행 중인지 확인
2. `.env.local`의 `NEXT_PUBLIC_API_URL` 확인
3. CORS 설정 확인 (백엔드 FastAPI)

## 📚 참고 자료

- [Next.js 문서](https://nextjs.org/docs)
- [Tailwind CSS 문서](https://tailwindcss.com/docs)
- [Zustand 문서](https://docs.pmnd.rs/zustand/getting-started/introduction)
- [React Three Fiber](https://docs.pmnd.rs/react-three-fiber/getting-started/introduction)

## 🤝 기여

이슈 및 PR 환영합니다!

## 📄 라이선스

MIT License
