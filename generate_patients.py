"""
사건 1: 중복 환자 탐지 - 1주차 (가짜 데이터 생성)

전략:
1. '진짜' 환자 N명을 만든다 (base_patients).
2. 그 중 일부를 골라서, 일부러 오타/표기차이/누락을 섞은 '중복 등록' 레코드를 추가로 만든다.
3. 최종 CSV에는 정답(같은 사람인지 여부)이 없다 -- 나중에 네가 매칭 로직으로 "몇 %를 맞췄는지" 채점할 때 쓰려고
   patient_uid (진짜 동일인 식별자)는 따로 answer_key.csv에 숨겨둔다.
   (실전에서는 이 정답을 모른 채로 시작하는 게 맞지만, 학습 단계에서는 채점을 위해 필요.)

실행: python generate_patients.py
결과: patients.csv (문제), answer_key.csv (정답, 채점할 때만 열어볼 것)
"""

import random
import csv
from faker import Faker

fake = Faker("ko_KR")
random.seed(42)
Faker.seed(42)

N_BASE_PATIENTS = 500       # '진짜' 사람 수
DUPLICATE_RATE = 0.15       # 이 중 15%는 중복 등록됨 (2~3번 등록)

def make_base_patient(uid: int) -> dict:
    return {
        "patient_uid": uid,          # 정답용 (실제 시스템엔 없는 값)
        "name": fake.name(),
        "birth_date": fake.date_of_birth(minimum_age=1, maximum_age=95).isoformat(),
        "phone": fake.phone_number(),
        "address": fake.address(),
    }

def noisy_copy(base: dict) -> dict:
    """같은 사람이지만 재등록 시 생긴 표기 차이를 흉내낸다."""
    name = base["name"]
    phone = base["phone"]
    address = base["address"]
    birth = base["birth_date"]

    noise_type = random.choice(["typo_name", "phone_format", "address_partial", "birth_typo", "clean_dup"])

    if noise_type == "typo_name" and len(name) > 1:
        i = random.randint(0, len(name) - 1)
        name = name[:i] + random.choice("가나다라마바사아자차") + name[i+1:]
    elif noise_type == "phone_format":
        phone = phone.replace("-", "")  # 하이픈 없이 저장된 경우
    elif noise_type == "address_partial":
        address = address.split(" ")[0] + " " + address.split(" ")[1] if len(address.split(" ")) > 1 else address
    elif noise_type == "birth_typo":
        # 월/일이 실수로 바뀌어 등록된 경우 (흔한 EMR 오입력 패턴)
        parts = birth.split("-")
        if len(parts) == 3:
            birth = f"{parts[0]}-{parts[2]}-{parts[1]}"
    # clean_dup: 완전히 동일하게 중복 등록된 경우 (제일 쉬운 케이스)

    return {
        "patient_uid": base["patient_uid"],
        "name": name,
        "birth_date": birth,
        "phone": phone,
        "address": address,
    }

def main():
    base_patients = [make_base_patient(i) for i in range(1, N_BASE_PATIENTS + 1)]

    all_records = list(base_patients)
    n_dupes = int(N_BASE_PATIENTS * DUPLICATE_RATE)
    dup_targets = random.sample(base_patients, n_dupes)

    for p in dup_targets:
        all_records.append(noisy_copy(p))
        # 일부는 3중 등록도 만든다
        if random.random() < 0.3:
            all_records.append(noisy_copy(p))

    random.shuffle(all_records)

    # patient_id: 시스템이 실제로 발급하는 등록번호 (patient_uid와 별개)
    for idx, r in enumerate(all_records, start=1):
        r["patient_id"] = f"P{idx:05d}"

    with open("patients.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", "name", "birth_date", "phone", "address"])
        writer.writeheader()
        for r in all_records:
            writer.writerow({k: r[k] for k in ["patient_id", "name", "birth_date", "phone", "address"]})

    with open("answer_key.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", "patient_uid"])
        writer.writeheader()
        for r in all_records:
            writer.writerow({"patient_id": r["patient_id"], "patient_uid": r["patient_uid"]})

    print(f"생성 완료: 총 {len(all_records)}건 (실제 인원 {N_BASE_PATIENTS}명, 중복 대상 {n_dupes}명)")
    print("patients.csv  -> 이걸로 매칭 로직을 짜세요 (정답 모르는 척 하고).")
    print("answer_key.csv -> 나중에 채점할 때만 여세요.")

if __name__ == "__main__":
    main()
