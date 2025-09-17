# MiniFlow API Workflow Test Guide

Bu rehber, MiniFlow API kullanarak komple bir workflow oluşturma ve test etme sürecini adım adım gösterir.

## Test Senaryosu
3 ardışık toplama işlemi yapan workflow:
1. **Node 1:** 2 + 2 = 4
2. **Node 2:** Node1_result + 2 = 6 (4 + 2)  
3. **Node 3:** Node2_result + 2 = 8 (6 + 2)

## Ön Koşul
```bash
cd /Users/enesa/PythonProjects/MiniFlow
python -m miniflow
```

---

## 1. Sistem Sağlık Kontrolü

```bash
curl -X GET "http://localhost:8000/health" \
  -H "accept: application/json"
```

**Beklenen Yanıt:**
```json
{"status":"healthy","service":"miniflow-api"}
```

---

## 2. Addition Script Oluşturma

```bash
curl -X POST "http://localhost:8000/api/bff/scripts/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "addition_script",
    "category": "math",
    "subcategory": "basic",
    "description": "Simple addition script for MiniFlow engine",
    "version": "1.0.0",
    "author": "MiniFlow Test",
    "file_extension": ".py",
    "content": "def module():\n    return AdditionModule()\n\nclass AdditionModule:\n    def run(self, context):\n        # Get parameters from context\n        num1 = context.get(\"num1\", 0)\n        num2 = context.get(\"num2\", 0)\n        \n        # Perform addition\n        result = num1 + num2\n        \n        # Return result in expected format\n        return {\n            \"sum\": result,\n            \"operation\": f\"{num1} + {num2} = {result}\"\n        }",
    "input_schema": {
      "type": "object",
      "properties": {
        "num1": {"type": "number", "description": "First number"},
        "num2": {"type": "number", "description": "Second number"}
      },
      "required": ["num1", "num2"]
    },
    "output_schema": {
      "type": "object", 
      "properties": {
        "sum": {"type": "number", "description": "Addition result"},
        "operation": {"type": "string", "description": "Operation description"}
      }
    },
    "test_input_params": {"num1": 2, "num2": 3},
    "test_output_params": {"sum": 5, "operation": "2 + 3 = 5"}
  }'
```

**Script ID'yi kaydedin:** `SC-XXXXXXXXXXXXX`

---

## 3. Workflow Oluşturma

```bash
curl -X POST "http://localhost:8000/api/bff/workflows/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "addition_chain_workflow",
    "description": "Test workflow with 3 sequential addition operations: 2+2, result+2, result+2",
    "priority": 10
  }'
```

**Workflow ID'yi kaydedin:** `WF-XXXXXXXXXXXXX`

---

## 4. Node'ları Oluşturma

### Node 1: 2 + 2

```bash
curl -X POST "http://localhost:8000/api/bff/nodes/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "name": "node_1_addition",
    "description": "First node: calculates 2 + 2",
    "script_id": "SC-XXXXXXXXXXXXX",
    "params": {
      "num1": 2,
      "num2": 2
    },
    "max_retries": 3,
    "timeout_seconds": 300
  }'
```

**Node 1 ID'yi kaydedin:** `ND-XXXXXXXXXXXXX`

### Node 2: Node1_result + 2

```bash
curl -X POST "http://localhost:8000/api/bff/nodes/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "name": "node_2_addition",
    "description": "Second node: adds result from node_1 + 2",
    "script_id": "SC-XXXXXXXXXXXXX",
    "params": {
      "num1": "{n{ND-XXXXXXXXXXXXX.sum}}",
      "num2": 2
    },
    "max_retries": 3,
    "timeout_seconds": 300
  }'
```

**Node 2 ID'yi kaydedin:** `ND-YYYYYYYYYYYYY`

### Node 3: Node2_result + 2

```bash
curl -X POST "http://localhost:8000/api/bff/nodes/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "name": "node_3_addition",
    "description": "Third node: adds result from node_2 + 2",
    "script_id": "SC-XXXXXXXXXXXXX",
    "params": {
      "num1": "{n{ND-YYYYYYYYYYYYY.sum}}",
      "num2": 2
    },
    "max_retries": 3,
    "timeout_seconds": 300
  }'
```

**Node 3 ID'yi kaydedin:** `ND-ZZZZZZZZZZZZZ`

---

## 5. Edge'leri (Bağlantıları) Oluşturma

### Edge 1: Node1 → Node2

```bash
curl -X POST "http://localhost:8000/api/bff/edges/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "from_node_id": "ND-XXXXXXXXXXXXX",
    "to_node_id": "ND-YYYYYYYYYYYYY",
    "condition_type": "SUCCESS"
  }'
```

### Edge 2: Node2 → Node3

```bash
curl -X POST "http://localhost:8000/api/bff/edges/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "from_node_id": "ND-YYYYYYYYYYYYY",
    "to_node_id": "ND-ZZZZZZZZZZZZZ",
    "condition_type": "SUCCESS"
  }'
```

---

## 6. Manual Trigger Oluşturma

```bash
curl -X POST "http://localhost:8000/api/bff/triggers/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "name": "manual_trigger_addition_chain",
    "trigger_type": "MANUAL",
    "description": "Manual trigger for testing addition chain workflow",
    "config": {
      "allow_parallel": false,
      "description": "Test trigger for sequential addition operations"
    },
    "status": "ACTIVE"
  }'
```

**Trigger ID'yi kaydedin:** `TR-XXXXXXXXXXXXX`

---

## 7. Workflow Çalıştırma (Manual Trigger)

```bash
curl -X POST "http://localhost:8000/api/bff/triggers/TR-XXXXXXXXXXXXX/execute" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "test_execution": true,
      "description": "Testing addition chain workflow: 2+2, result+2, result+2"
    }
  }'
```

**Execution ID'yi kaydedin:** `EX-XXXXXXXXXXXXX`

---

## 8. Execution Monitoring

### Execution Durumunu Kontrol Et

```bash
curl -X GET "http://localhost:8000/api/bff/executions/EX-XXXXXXXXXXXXX" \
  -H "accept: application/json"
```

### Execution Inputs Kontrol Et

```bash
curl -X GET "http://localhost:8000/api/bff/execution-inputs/?skip=0&limit=10" \
  -H "accept: application/json"
```

### Execution Outputs Kontrol Et

```bash
curl -X GET "http://localhost:8000/api/bff/execution-outputs/?skip=0&limit=10" \
  -H "accept: application/json"
```

---

## 9. Beklenen Sonuçlar

Workflow başarıyla tamamlandığında aşağıdaki sonuçları göreceksiniz:

### Final Execution Status:
```json
{
  "status": "COMPLETED",
  "results": {
    "ND-XXXXXXXXXXXXX": {
      "status": "SUCCESS",
      "result_data": {
        "sum": 4,
        "operation": "2 + 2 = 4"
      }
    },
    "ND-YYYYYYYYYYYYY": {
      "status": "SUCCESS", 
      "result_data": {
        "sum": 6,
        "operation": "4 + 2 = 6"
      }
    },
    "ND-ZZZZZZZZZZZZZ": {
      "status": "SUCCESS",
      "result_data": {
        "sum": 8,
        "operation": "6 + 2 = 8"
      }
    }
  }
}
```

---

## 10. Kritik Özellikler

### ✅ **Parametre Referansları:**
- `{n{node_id.variable_name}}` formatı ile önceki node sonuçlarını kullanma
- Node 2: `{n{ND-XXXXXXXXXXXXX.sum}}` → Node 1'in sum değerini alır
- Node 3: `{n{ND-YYYYYYYYYYYYY.sum}}` → Node 2'nin sum değerini alır

### ✅ **Dependency Management:**
- Node'lar dependency_count'una göre sıralı çalışır
- Node 1: dependency_count=0 (hemen çalışır)
- Node 2: dependency_count=1 (Node 1 tamamlandıktan sonra)
- Node 3: dependency_count=1 (Node 2 tamamlandıktan sonra)

### ✅ **Engine Integration:**
- Input Handler task'ları engine'e gönderir
- Engine script'leri çalıştırır
- Output Handler sonuçları işler ve dependency'leri günceller

---

## 11. Troubleshooting

### Yaygın Sorunlar:

1. **Port 8000 kullanımda:**
   ```bash
   lsof -i :8000
   kill -9 <PID>
   ```

2. **MiniFlow durmuş:**
   ```bash
   python -m miniflow
   ```

3. **Execution takılı:**
   - Input/Output handler loglarını kontrol edin
   - Execution inputs/outputs'u inceleyin

---

## 12. Test Başarı Kriterleri

✅ **Script başarıyla oluşturuldu**  
✅ **Workflow ve node'lar oluşturuldu**  
✅ **Edge'ler doğru bağlandı**  
✅ **Trigger oluşturuldu ve çalıştırıldı**  
✅ **Node'lar sıralı olarak çalıştı**  
✅ **Parametre referansları çözüldü**  
✅ **Final sonuç: 2+2=4, 4+2=6, 6+2=8**  

Bu test'in başarıyla tamamlanması, MiniFlow'un production-ready olduğunu ve karmaşık workflow'ları yönetebileceğini gösterir! 🎉
