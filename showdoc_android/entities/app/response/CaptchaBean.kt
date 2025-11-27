package com.cqfengli.api.entities.app.response

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

/**
 * 图片验证码 (CaptchaBean)
 * 
 * 接口文档: https://doc.cqfengli.com/web/#/90/4463
 * 
 * 成功返回示例:
 * {
 *   "code": 1,
 *   "msg": "请求成功",
 *   "data": {
 *     "base64": "data:image/png;base64,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\r\n"
 *   }
 * }
 */
@Parcelize
data class CaptchaBean(
    var base64: String
) : Parcelable