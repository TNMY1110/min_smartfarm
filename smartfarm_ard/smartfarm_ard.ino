#include <DHT.h>

#define DHT_PIN 8   // D2
#define DHT_TYPE DHT11  //
#define SOIL_PIN A0
#define FAN_PIN 9

// 임계값 설정
#define HUMID_HIGH 70.0   // 습도 70% 이상이면 팬 강하게
#define HUMID_MID  55.0   // 55% 이상이면 팬 약하게
#define SOIL_DRY   600    // 토양 수분 낮으면 건조 판단 (0~1023)

DHT dht(DHT_PIN, DHT_TYPE);

void setup() 
{
  Serial.begin(9600);
  pinMode(FAN_PIN, OUTPUT);
  dht.begin();
  Serial.println("=== 스마트팜 센서 시작 ===");
}

void loop() 
{
  // 센서 읽기
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  int soilRaw = analogRead(SOIL_PIN);

  // 읽기 실패 체크
  if (isnan(humidity) || isnan(temperature)) 
  {
    Serial.println("[ERROR] DHT11 읽기 실패");
    delay(2000);
    return;
  }

  // 토양 수분 % 변환 (건조=0%, 수분=100%)
  int soilPercent = map(soilRaw, 1023, 0, 100, 0);

  // 팬 PWM 제어
  int fanSpeed = 0;

  if (humidity >= HUMID_HIGH) 
  {
    fanSpeed = 255;         // 최대 속도
  }

  else if (humidity >= HUMID_MID) 
  {
    fanSpeed = 150;         // 중간 속도
  }

  else 
  {
    fanSpeed = 0;           // 정지
  }
  
  analogWrite(FAN_PIN, fanSpeed);

  // 시리얼 출력 (나중에 MQTT/Python에서 파싱)
  Serial.print("TEMP:");
  Serial.print(temperature);
  Serial.print(",HUMID:");
  Serial.print(humidity);
  Serial.print(",SOIL:");
  Serial.print(soilPercent);
  Serial.print(",FAN:");
  Serial.println(fanSpeed);

  delay(2000); // 2초마다 측정
}
