function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    
    // 1) 4번 탭: 실제 성적(xG, xA 포함) 사후 업데이트 요청
    if (data.action === "update_actual") {
      var valSheet = ss.getSheetByName("검증데이터");
      if (!valSheet) {
        return ContentService.createTextOutput(JSON.stringify({status: "error", message: "검증데이터 시트가 없습니다."}))
          .setMimeType(ContentService.MimeType.JSON);
      }
      
      var rows = valSheet.getDataRange().getValues();
      var updated = false;
      
      for (var i = 1; i < rows.length; i++) {
        if (rows[i][1] == data.season && rows[i][2] == data.name) {
          valSheet.getRange(i + 1, 12).setValue(data.act_mins);    // L열: 실제출전시간
          valSheet.getRange(i + 1, 13).setValue(data.act_goals);   // M열: 실제득점
          valSheet.getRange(i + 1, 14).setValue(data.act_xg);      // N열: 실제xG (추가)
          valSheet.getRange(i + 1, 15).setValue(data.act_assists); // O열: 실제도움
          valSheet.getRange(i + 1, 16).setValue(data.act_xa);      // P열: 실제xA (추가)
          valSheet.getRange(i + 1, 17).setValue(data.act_rating);  // Q열: 실제평점
          valSheet.getRange(i + 1, 18).setValue(data.notes || ""); // R열: 검증메모
          updated = true;
          break;
        }
      }
      
      if (updated) {
        return ContentService.createTextOutput(JSON.stringify({status: "success", message: "실제 성적(xG/xA 포함) 업데이트 완료"}))
          .setMimeType(ContentService.MimeType.JSON);
      } else {
        return ContentService.createTextOutput(JSON.stringify({status: "not_found", message: "해당 시즌의 선수 예측 데이터를 찾을 수 없습니다."}))
          .setMimeType(ContentService.MimeType.JSON);
      }
    }
    
    // 2) 2번 탭: 최초 저장 시 (메인 시트 + 검증데이터 동시 기록)
    var mainSheet = ss.getSheets()[0];
    mainSheet.appendRow([
      data.date, data.season, data.name, data.nat, data.age, data.pos, data.from_league,
      data.buying_tier, data.transfer_type, data.tm_val, data.fee, data.fair_val,
      data.diff, data.status, data.deal_score,
      data.prev_matches, data.prev_mins, data.prev_goals, data.prev_xg, data.prev_assists,
      data.prev_xa, data.prev_shots, data.prev_sot, data.prev_chances, data.prev_dribbles,
      data.prev_touches_box, data.prev_tackles, data.prev_rating,
      data.to_league, data.proj_mins, data.proj_goals, data.proj_xg, data.proj_assists,
      data.proj_xa, data.proj_shots, data.proj_rating,
      data.notes
    ]);
    
    var valSheet = ss.getSheetByName("검증데이터");
    if (valSheet) {
      valSheet.appendRow([
        data.date, data.season, data.name, data.pos, data.to_league,
        data.proj_mins, data.proj_goals, data.proj_xg, data.proj_assists, data.proj_xa, data.proj_rating,
        "", "", "", "", "", "", "" // 실제 성적 열(L~R)은 최초 저장 시 빈칸 유지
      ]);
    }
    
    return ContentService.createTextOutput(JSON.stringify({status: "success"}))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({status: "error", message: error.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
