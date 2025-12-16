# Part 6 - Step 13: 사용자 준비 사항 (User End)

## ⚠️ 중요: 이 단계는 사용자가 직접 수행해야 합니다!

---

## 1. IBKR Paper Trading 계좌 준비

### 1.1 Paper 계좌 확인
- IBKR 웹사이트 로그인
- Paper Trading 계좌가 활성화되어 있는지 확인
- Paper 계좌 잔고 확인 (가상 자금)

### 1.2 IB Gateway 설치 (아직 안 했다면)
- [다운로드 링크](https://www.interactivebrokers.com/en/trading/ibgateway-stable.php)
- 설치 후 재시작

---

## 2. IB Gateway 설정

### 2.1 IB Gateway 실행
1. IB Gateway 실행
2. **Paper Trading** 모드 선택
3. 로그인

### 2.2 API 설정 (Configure → Settings → API)
- ✅ **Enable ActiveX and Socket Clients** 체크
- ✅ **Socket port:** `4002` (Paper 기본)
- ✅ **Allow connections from localhost only** 체크
- ✅ **Read-Only API** 체크 해제 (주문 필요)

### 2.3 설정 저장
- Apply 클릭
- Gateway 재시작

---

## 3. .env 파일 확인

프로젝트 루트의 `.env` 파일에 다음 내용이 있는지 확인:

```env
IB_HOST=127.0.0.1
IB_PORT=4002
IB_CLIENT_ID=1
IB_ACCOUNT=DU1234567  # 실제 Paper 계좌번호로 변경!
```

---

## 4. 테스트 실행 준비 완료 체크리스트

- [ ] IB Gateway 실행 중
- [ ] Paper Trading 모드로 로그인됨
- [ ] API 설정 완료 (포트 4002)
- [ ] .env 파일에 계좌번호 입력됨
- [ ] 가상환경 활성화됨 (.venv)

---

## 5. 테스트 시작

모든 체크리스트 완료 후:

```powershell
cd d:\Codes\Omnissiah-1.0
.venv\Scripts\activate
python main.py
```

GUI에서:
1. **Start** 버튼 클릭
2. "IBKR 연결됨" 확인
3. 레짐/VIX 정보 업데이트 확인

---

## 🚨 문제 발생 시

### 연결 실패
- Gateway가 실행 중인지 확인
- 포트 4002가 맞는지 확인
- 방화벽 설정 확인

### 주문 거부
- Paper 계좌 잔고 확인
- Read-Only API가 해제되었는지 확인
- 계좌번호가 정확한지 확인
