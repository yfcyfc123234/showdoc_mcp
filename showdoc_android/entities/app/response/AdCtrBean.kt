package com.cqfengli.api.entities.app.response

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

/**
 * 弹窗广告控制 (AdCtrBean)
 * 
 * 接口文档: https://doc.cqfengli.com/web/#/90/5476
 * 
 * 成功返回示例:
 * {
 *   "code": 1,
 *   "msg": "请求成功",
 *   "data": {
 *     "show": 1
 *   },
 *   "hasNext": 0
 * }
 */
@Parcelize
data class AdCtrBean(
    var show: Int
) : Parcelable