# MiniFlow Trigger Input Workflow - Adım Adım Rehber

Bu rehber, MiniFlow API kullanarak trigger'dan değer alan workflow oluşturma sürecini adım adım gösterir.

## Test Senaryosu
Trigger'dan `base_number` alan ve 3 ardışık işlem yapan workflow:
1. **Trigger Input:** `base_number = 7`
2. **Node 1:** `{t{trigger.base_number}} + 3` = `7 + 3 = 10`
3. **Node 2:** `Node1_result + 4` = `10 + 4 = 14`
4. **Node 3:** `Node2_result + 2` = `14 + 2 = 16`

## Ön Koşul
MiniFlow sisteminin çalışıyor olması:
```bash
cd /Users/enesa/PythonProjects/MiniFlow
python -m miniflow
```

---

## Adım 1: Sistem Sağlık Kontrolü

**Amaç:** MiniFlow API'nin çalışıp çalışmadığını kontrol etmek

```bash
curl -X GET "http://localhost:8000/health" \
  -H "accept: application/json"
```

**Beklenen Yanıt:**
```json
{
  "status": "healthy",
  "service": "miniflow-api"
}
```

**✅ Başarı Kriteri:** Status 200 ve healthy yanıtı

---

## Adım 2: Addition Script Kontrolü

**Amaç:** Daha önce oluşturulan addition script'inin mevcut olduğunu doğrulamak

```bash
curl -X GET "http://localhost:8000/api/bff/scripts/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json"
```

**Not:** Eğer script yoksa, önce script oluşturmanız gerekir (önceki guide'a bakın)

**Script ID'yi kaydedin:** `SC-XXXXXXXXXXXXX`

---

## Adım 3: Yeni Workflow Oluşturma

**Amaç:** Trigger input'u kullanan yeni bir workflow oluşturmak

```bash
curl -X POST "http://localhost:8000/api/bff/workflows/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "trigger_input_workflow",
    "description": "Workflow that takes base number from trigger input and processes it through 3 nodes",
    "priority": 15
  }'
```

**Yanıt Örneği:**
```json
{
  "success": true,
  "data": {
    "action_status": true,
    "record_id": "WF-7D6DFD87C2AE41B1A",
    "message": "Workflow creation successful"
  }
}
```

**📝 Kaydet:** Workflow ID = `WF-7D6DFD87C2AE41B1A`

---

## Adım 4: Node 1 Oluşturma (Trigger Input Kullanan)

**Amaç:** Trigger'dan `base_number` alan ve +3 yapan ilk node

```bash
curl -X POST "http://localhost:8000/api/bff/nodes/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "WF-7D6DFD87C2AE41B1A",
    "name": "trigger_input_node",
    "description": "First node: takes base_number from trigger and adds 3",
    "script_id": "SC-23D8F2FF59D84A77B",
    "params": {
      "num1": "{t{trigger.base_number}}",
      "num2": 3
    },
    "max_retries": 3,
    "timeout_seconds": 300
  }'
```

**⚠️ Önemli Notlar:**
- `"num1": "{t{trigger.base_number}}"` - Trigger'dan base_number değerini alır
- `{t{trigger.variable_name}}` formatı kullanılır
- `script_id` değerini kendi script ID'nizle değiştirin

**Yanıt Örneği:**
```json
{
  "success": true,
  "data": {
    "record_id": "ND-86D63595FA294BC4A"
  }
}
```

**📝 Kaydet:** Node 1 ID = `ND-86D63595FA294BC4A`

---

## Adım 5: Node 2 Oluşturma (Node 1 Sonucunu Kullanan)

**Amaç:** Node 1'in sonucunu alıp +4 yapan ikinci node

```bash
curl -X POST "http://localhost:8000/api/bff/nodes/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "WF-7D6DFD87C2AE41B1A",
    "name": "second_addition_node",
    "description": "Second node: adds 4 to the result from trigger_input_node",
    "script_id": "SC-23D8F2FF59D84A77B",
    "params": {
      "num1": "{n{ND-86D63595FA294BC4A.sum}}",
      "num2": 4
    },
    "max_retries": 3,
    "timeout_seconds": 300
  }'
```

**⚠️ Önemli Notlar:**
- `"num1": "{n{ND-86D63595FA294BC4A.sum}}"` - Node 1'in sum sonucunu alır
- `{n{node_id.variable_name}}` formatı kullanılır
- Node 1 ID'yi kendi ID'nizle değiştirin

**Yanıt Örneği:**
```json
{
  "success": true,
  "data": {
    "record_id": "ND-D83864E4C76A4A4EA"
  }
}
```

**📝 Kaydet:** Node 2 ID = `ND-D83864E4C76A4A4EA`

---

## Adım 6: Node 3 Oluşturma (Node 2 Sonucunu Kullanan)

**Amaç:** Node 2'nin sonucunu alıp +2 yapan üçüncü node

```bash
curl -X POST "http://localhost:8000/api/bff/nodes/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "WF-7D6DFD87C2AE41B1A",
    "name": "final_addition_node",
    "description": "Third node: adds 2 to the result from second_addition_node",
    "script_id": "SC-23D8F2FF59D84A77B",
    "params": {
      "num1": "{n{ND-D83864E4C76A4A4EA.sum}}",
      "num2": 2
    },
    "max_retries": 3,
    "timeout_seconds": 300
  }'
```

**⚠️ Önemli Notlar:**
- `"num1": "{n{ND-D83864E4C76A4A4EA.sum}}"` - Node 2'nin sum sonucunu alır
- Node 2 ID'yi kendi ID'nizle değiştirin

**Yanıt Örneği:**
```json
{
  "success": true,
  "data": {
    "record_id": "ND-4878FA7C63A543CAB"
  }
}
```

**📝 Kaydet:** Node 3 ID = `ND-4878FA7C63A543CAB`

---

## Adım 7: Edge 1 Oluşturma (Node 1 → Node 2)

**Amaç:** Node 1'den Node 2'ye bağlantı kurmak

```bash
curl -X POST "http://localhost:8000/api/bff/edges/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "WF-7D6DFD87C2AE41B1A",
    "from_node_id": "ND-86D63595FA294BC4A",
    "to_node_id": "ND-D83864E4C76A4A4EA",
    "condition_type": "SUCCESS"
  }'
```

**⚠️ Önemli Notlar:**
- `from_node_id` ve `to_node_id` değerlerini kendi Node ID'lerinizle değiştirin
- `condition_type: "SUCCESS"` - Node başarılı olduğunda geçişi sağlar

**Yanıt Örneği:**
```json
{
  "success": true,
  "data": {
    "record_id": "ED-B5926AC60FEA4D48B"
  }
}
```

---

## Adım 8: Edge 2 Oluşturma (Node 2 → Node 3)

**Amaç:** Node 2'den Node 3'e bağlantı kurmak

```bash
curl -X POST "http://localhost:8000/api/bff/edges/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "WF-7D6DFD87C2AE41B1A",
    "from_node_id": "ND-D83864E4C76A4A4EA",
    "to_node_id": "ND-4878FA7C63A543CAB",
    "condition_type": "SUCCESS"
  }'
```

**⚠️ Önemli Notlar:**
- Node ID'leri kendi değerlerinizle değiştirin

**Yanıt Örneği:**
```json
{
  "success": true,
  "data": {
    "record_id": "ED-322BAF5C3F764F6B8"
  }
}
```

---

## Adım 9: Manual Trigger Oluşturma

**Amaç:** Input data alabilen manual trigger oluşturmak

```bash
curl -X POST "http://localhost:8000/api/bff/triggers/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "WF-7D6DFD87C2AE41B1A",
    "name": "trigger_with_input_data",
    "trigger_type": "MANUAL",
    "description": "Manual trigger that provides base_number input for the workflow",
    "config": {
      "allow_parallel": false,
      "description": "Trigger with input data support"
    },
    "status": "ACTIVE"
  }'
```

**Yanıt Örneği:**
```json
{
  "success": true,
  "data": {
    "record_id": "TR-714E791540524AA7B"
  }
}
```

**📝 Kaydet:** Trigger ID = `TR-714E791540524AA7B`

---

## Adım 10: Workflow Özeti Kontrolü

**Amaç:** Oluşturulan workflow'un doğruluğunu kontrol etmek

### Workflow'u Görüntüle:
```bash
curl -X GET "http://localhost:8000/api/bff/workflows/WF-7D6DFD87C2AE41B1A" \
  -H "accept: application/json"
```

### Node'ları Listele:
```bash
curl -X GET "http://localhost:8000/api/bff/nodes/?skip=0&limit=10" \
  -H "accept: application/json"
```

### Edge'leri Listele:
```bash
curl -X GET "http://localhost:8000/api/bff/edges/?skip=0&limit=10" \
  -H "accept: application/json"
```

---

## Adım 11: Workflow Çalıştırma (Trigger Input ile)

**Amaç:** Trigger'a `base_number=7` göndererek workflow'u başlatmak

```bash
curl -X POST "http://localhost:8000/api/bff/triggers/TR-714E791540524AA7B/execute" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "base_number": 7,
      "test_description": "Testing trigger input: base_number=7, expected flow: 7+3=10, 10+4=14, 14+2=16"
    }
  }'
```

**⚠️ Önemli Notlar:**
- `base_number: 7` - Bu değer Node 1'de `{t{trigger.base_number}}` olarak kullanılacak
- Trigger ID'yi kendi değerinizle değiştirin
- İstediğiniz başka değerler ekleyebilirsiniz

**Yanıt Örneği:**
```json
{
  "success": true,
  "data": {
    "trigger_id": "TR-714E791540524AA7B",
    "workflow_id": "WF-7D6DFD87C2AE41B1A",
    "execution_id": "EX-12F098DD70D74",
    "execution_status": "PENDING"
  }
}
```

**📝 Kaydet:** Execution ID = `EX-12F098DD70D74`

---

## Adım 12: Execution Monitoring

**Amaç:** Workflow'un ilerleyişini takip etmek

### İlk Durum Kontrolü (hemen):
```bash
curl -X GET "http://localhost:8000/api/bff/executions/EX-12F098DD70D74" \
  -H "accept: application/json"
```

### 5 Saniye Sonra Kontrol:
```bash
sleep 5 && curl -X GET "http://localhost:8000/api/bff/executions/EX-12F098DD70D74" \
  -H "accept: application/json"
```

### 10 Saniye Sonra Final Kontrol:
```bash
sleep 10 && curl -X GET "http://localhost:8000/api/bff/executions/EX-12F098DD70D74" \
  -H "accept: application/json"
```

**⚠️ Önemli Notlar:**
- Execution ID'yi kendi değerinizle değiştirin
- Status `PENDING` → `COMPLETED` değişmesini bekleyin

---

## Adım 13: Execution Inputs İnceleme

**Amaç:** Task'ların nasıl hazırlandığını görmek

```bash
curl -X GET "http://localhost:8000/api/bff/execution-inputs/?skip=0&limit=10" \
  -H "accept: application/json"
```

**Bu size şunları gösterecek:**
- Her node'un `dependency_count` değeri
- Parameter'ların nasıl çözüldüğü
- Node'ların execution sırası

---

## Adım 14: Execution Outputs İnceleme

**Amaç:** Her node'un sonuçlarını detaylı görmek

```bash
curl -X GET "http://localhost:8000/api/bff/execution-outputs/?skip=0&limit=10" \
  -H "accept: application/json"
```

---

## Adım 15: Beklenen vs Gerçek Sonuçlar

### Beklenen Sonuçlar:
```
Node 1: trigger.base_number(7) + 3 = 10
Node 2: Node1.sum(10) + 4 = 14  
Node 3: Node2.sum(14) + 2 = 16
```

### Final Execution Response (COMPLETED durumunda):
```json
{
  "status": "COMPLETED",
  "results": {
    "ND-86D63595FA294BC4A": {
      "status": "SUCCESS",
      "result_data": {
        "sum": 10,
        "operation": "7 + 3 = 10"
      }
    },
    "ND-D83864E4C76A4A4EA": {
      "status": "SUCCESS", 
      "result_data": {
        "sum": 14,
        "operation": "10 + 4 = 14"
      }
    },
    "ND-4878FA7C63A543CAB": {
      "status": "SUCCESS",
      "result_data": {
        "sum": 16,
        "operation": "14 + 2 = 16"
      }
    }
  }
}
```

---

## Parametrik Test: Farklı Değerlerle Test

### Test 1: base_number = 5
```bash
curl -X POST "http://localhost:8000/api/bff/triggers/TR-714E791540524AA7B/execute" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "base_number": 5,
      "test_description": "Testing with base_number=5: 5+3=8, 8+4=12, 12+2=14"
    }
  }'
```

**Beklenen:** `5 → 8 → 12 → 14`

### Test 2: base_number = 10
```bash
curl -X POST "http://localhost:8000/api/bff/triggers/TR-714E791540524AA7B/execute" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "base_number": 10,
      "test_description": "Testing with base_number=10: 10+3=13, 13+4=17, 17+2=19"
    }
  }'
```

**Beklenen:** `10 → 13 → 17 → 19`

---

## Troubleshooting

### Yaygın Sorunlar ve Çözümleri:

#### 1. Trigger Reference Çalışmıyor
**Semptom:** Node 1'de trigger değeri çözülmüyor
**Çözüm:** 
- Trigger format'ını kontrol edin: `{t{trigger.base_number}}`
- Trigger execution'da `input_data` içinde `base_number` olduğundan emin olun

#### 2. Node Reference Çalışmıyor  
**Semptom:** Node 2/3'te önceki node değerleri çözülmüyor
**Çözüm:**
- Node format'ını kontrol edin: `{n{NODE_ID.sum}}`
- Node ID'lerin doğru olduğundan emin olun

#### 3. Execution Takılı Kalıyor
**Semptom:** Status sürekli PENDING kalıyor
**Çözüm:**
- Input Handler ve Output Handler loglarını kontrol edin
- MiniFlow servislerinin çalıştığından emin olun

#### 4. Script Path Hatası
**Semptom:** "Script file not found" hatası
**Çözüm:**
- Script'in doğru oluşturulduğunu kontrol edin
- Script ID'nin doğru olduğundan emin olun

---

## Başarı Kriterleri

### ✅ Tamamlanması Gereken Kontrollar:

1. **✅ Workflow Oluşturuldu:** WF-XXXXXXXXXXXXX ID'si alındı
2. **✅ 3 Node Oluşturuldu:** Her biri farklı parametre türü kullanıyor
3. **✅ 2 Edge Oluşturuldu:** Sequential flow sağlanıyor
4. **✅ Trigger Oluşturuldu:** Input data kabul ediyor
5. **✅ Execution Başlatıldı:** Trigger başarıyla çalıştırıldı
6. **✅ Trigger Input Çözüldü:** `{t{trigger.base_number}}` → `7`
7. **✅ Node References Çözüldü:** `{n{node.sum}}` değerleri doğru
8. **✅ Sequential Execution:** Node'lar sıralı çalıştı
9. **✅ Final Result:** `7 → 10 → 14 → 16` akışı tamamlandı
10. **✅ Status COMPLETED:** Workflow başarıyla bitti

---

## Özet

Bu rehber şunları gösterir:

### 🎯 **Teknik Başarılar:**
- **Trigger Input Integration:** Trigger'dan parametre alma
- **Mixed Reference Types:** Trigger + Node referansları
- **Sequential Dependency:** Doğru execution sırası
- **Real-time Processing:** Canlı workflow işleme

### 📊 **Test Senaryosu:**
- **Input:** `base_number = 7`
- **Flow:** `7 + 3 = 10`, `10 + 4 = 14`, `14 + 2 = 16`
- **Output:** Final sum = 16

### 🚀 **MiniFlow Özellikleri:**
- **Dynamic Parameter Resolution:** Runtime'da parametre çözme
- **Robust State Management:** Execution state tracking
- **Flexible Trigger System:** Çeşitli input türleri
- **Production Ready:** Enterprise-level workflow management

Bu test'in başarıyla tamamlanması, MiniFlow'un gerçek dünya senaryolarında kullanılabileceğini kanıtlar! 🎉
