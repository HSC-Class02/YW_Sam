[![🔗 대시보드 바로가기](https://img.shields.io/badge/🔗%20대시보드%20바로가기-OPEN%20DASHBOARD-174EA6?style=for-the-badge)](https://hsc-class02.github.io/YW_Sam/)

# 삼성전자 재무 데이터 대시보드

OpenDART 정기공시를 이용해 삼성전자(005930)의 주요 재무수치와 재무비율을 수집·시각화합니다. 대시보드는 연간, 반기, 분기 데이터를 구분해 보여주며 PDF 인쇄와 Excel 다운로드를 지원합니다.

## 시작하기

1. OpenDART에서 API 인증키를 발급합니다: https://opendart.fss.or.kr/
2. 저장소의 **Settings → Secrets and variables → Actions**에서 새 repository secret을 등록합니다. 이름은 **OPENDART_API_KEY**를 권장하며, 기존 설정과의 호환을 위해 **DART_API_KEY**도 지원합니다. 값에는 OpenDART에서 발급한 40자리 키를 입력합니다. 키를 코드나 README에 직접 기록하지 마세요.
3. **Actions → Update and Deploy → Run workflow**를 실행합니다. 이후 매월 1일 UTC 00:20(한국시간 09:20)에 데이터 수집과 배포가 자동 실행됩니다.
4. **Settings → Pages**에서 Build and deployment의 Source가 **GitHub Actions**인지 확인합니다.

키를 등록했는데 수집 단계가 건너뛰어진다면 secret 이름이 위 두 이름 중 하나인지, 그리고 repository 또는 **github-pages environment**에 Actions secret으로 등록했는지 확인하세요. 워크플로우 실행 로그에서 실제 수집 건수도 검증합니다.

OpenDART 전체 재무제표 API는 2015년 이후 자료를 제공합니다. 과거 공시의 데이터 유무와 회사가 보고한 계정명에 따라 일부 값은 비어 있을 수 있습니다. 누락값은 0으로 대체하지 않습니다.

## 대시보드 기능

- 주요 지표 카드 및 연간/분기 추세 그래프
- 연간(Annual), 반기(Half-year), 분기(Quarterly)별 상세 재무 테이블
- 페이지 내 데이터 내보내기 도구에서 화면 인쇄/PDF 저장 및 기간별 Excel 내보내기
- OpenDART 기반 월간 데이터 갱신
- 하단 국내 peer firms 비교 참고표

## 재무 항목과 해석

금액은 원 단위 원천자료를 대시보드에서 조 원 단위로 표시합니다. 분기 손익 및 현금흐름은 분기보고서·반기보고서·사업보고서의 누적 수치 차이로 계산합니다. 자산, 부채, 자본 등 재무상태표 항목은 각 분기말 시점의 보고값을 사용합니다. 분기 마진은 해당 분기의 값이며 연환산 값이 아닙니다.

주요 항목: 매출액, 매출원가, 매출총이익, 영업이익, 법인세비용차감전순이익, 당기순이익, 유동자산, 자산총계, 유동부채, 부채총계, 자본총계, 영업·투자·재무활동 현금흐름 및 주요 재무비율.

## 데이터 원천

- 금융감독원 전자공시 OpenDART: https://opendart.fss.or.kr/
- 단일회사 전체 재무제표 API: https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019020
- 대상 법인 고유번호: 00126380 (삼성전자)

## 국내 Peer Firms

아래 기업은 반도체·전자제품·부품 및 디스플레이 분야의 국내 상장 비교 참고군입니다. 사업 구조가 서로 다르므로 완전한 동종기업 집단이나 투자 추천을 의미하지 않습니다.

| 기업 | 종목코드 | 주요 비교 영역 | 공식 웹사이트 |
|---|---:|---|---|
| SK하이닉스 | 000660 | 메모리 반도체, HBM | [바로가기](https://www.skhynix.com/) |
| LG전자 | 066570 | 완제품, 가전, 전장 | [바로가기](https://www.lge.co.kr/) |
| 삼성전기 | 009150 | 전자부품, 기판, MLCC | [바로가기](https://www.samsungsem.com/) |
| LG디스플레이 | 034220 | 디스플레이 패널 | [바로가기](https://www.lgdisplay.com/) |
| DB하이텍 | 000990 | 파운드리, 아날로그 반도체 | [바로가기](https://www.dbhitek.com/) |
| 한미반도체 | 042700 | 반도체 후공정 장비 | [바로가기](https://www.hanmisemi.com/) |
| ISC | 095340 | 반도체 테스트 소켓 | [바로가기](https://www.isc21.kr/) |
| 솔브레인 | 357780 | 반도체 공정 소재 | [바로가기](https://www.soulbrain.co.kr/) |
| 삼성SDI | 006400 | 배터리 및 전자소재 | [바로가기](https://www.samsungsdi.com/) |

## 프로젝트 구조

- index.html: 대시보드 UI, 그래프, 상세 테이블, PDF/Excel 도구
- scripts/update_financials.py: OpenDART 데이터 수집·정규화·CSV/JSON 생성
- data/annual.csv: 연간 데이터
- data/halfyear.csv: 반기 데이터
- data/quarterly.csv: 분기 데이터
- data/metrics.json: 대시보드용 데이터
- .github/workflows/update-and-deploy.yml: 월간 자동 수집 및 GitHub Pages 배포

## 문제 해결

- 대시보드에 데이터가 없으면 OPENDART_API_KEY 또는 DART_API_KEY secret 등록 여부와 최신 Actions 실행 로그를 확인하세요.
- 워크플로우는 데이터 수집 후 결과 건수를 검증합니다. 0건 또는 삼성전자 종목이 아닌 데이터면 배포 단계로 진행하지 않습니다.
- OpenDART API는 요청 제한 또는 일시적인 서비스 오류를 반환할 수 있습니다. 오류 시 워크플로우 로그에 원인이 표시됩니다.
- About 영역의 Homepage 링크는 저장소 페이지 오른쪽 **About → Edit**에서 https://hsc-class02.github.io/YW_Sam/ 으로 설정하세요.
