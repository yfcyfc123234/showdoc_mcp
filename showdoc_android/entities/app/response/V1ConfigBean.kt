package com.cqfengli.api.entities.app.response

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

/**
 * 应用配置 (V1ConfigBean)
 * 
 * 接口文档: https://doc.cqfengli.com/web/#/90/4455
 * 
 * 成功返回示例:
 * {
 *   "code": 1,
 *   "msg": "请求成功",
 *   "data": {
 *     "name": "已读不想回",
 *     "baseacturl": "http://notreply.uxiu.vip",
 *     "status": 0,
 *     "version": "1.0.0",
 *     "refuseMsg": "请阅读并同意《隐私政策》和《用户协议》，或者退出APP",
 *     "kpff": 0,
 *     "ad": 1,
 *     "kf": "https://kf.teizhe.com/chatIndex?app=notreply&extra=",
 *     "yzm": "http://yzm.cqfengli.com",
 *     "privacypolicy": "http://notreply.uxiu.vip/privacypolicy",
 *     "useragreement": "http://notreply.uxiu.vip/useragreement",
 *     "notify_manage": {
 *       "game": "https://xinan1.zos.ctyun.cn/notreply/notify/video_game.mp4",
 *       "scrolling": "https://xinan1.zos.ctyun.cn/notreply/notify/video_scrolling.mp4",
 *       "voice": "https://xinan1.zos.ctyun.cn/notreply/notify/video_voice.mp4",
 *       "screen": "https://xinan1.zos.ctyun.cn/notreply/notify/video_screen.mp4"
 *     },
 *     "island": {
 *       "xiaomi": "https://xinan1.zos.ctyun.cn/notreply/island/petal_20241231_162346.mp4",
 *       "vivo": "https://xinan1.zos.ctyun.cn/notreply/island/petal_20241231_151947.mp4",
 *       "huawei": "https://xinan1.zos.ctyun.cn/notreply/island/petal_20241231_170150.mp4",
 *       "oppo": "https://xinan1.zos.ctyun.cn/notreply/island/petal_20241231_162704.mp4"
 *     },
 *     "recommend": {
 *       "is_on": 0,
 *       "download_url": ""
 *     }
 *   },
 *   "hasNext": 0
 * }
 */
@Parcelize
data class V1ConfigBean(
    var name: String,
    var baseacturl: String,
    var status: Int,
    var version: String,
    var refuseMsg: String,
    var kpff: Int,
    var ad: Int,
    var kf: String,
    var yzm: String,
    var privacypolicy: String,
    var useragreement: String,
    var notify_manage: NotifyManageBean,
    var island: IslandBean,
    var recommend: RecommendBean
) : Parcelable


/**
 * NotifyManageBean
 */
@Parcelize
data class NotifyManageBean(
    var game: String,
    var scrolling: String,
    var voice: String,
    var screen: String
) : Parcelable

/**
 * IslandBean
 */
@Parcelize
data class IslandBean(
    var xiaomi: String,
    var vivo: String,
    var huawei: String,
    var oppo: String
) : Parcelable

/**
 * RecommendBean
 */
@Parcelize
data class RecommendBean(
    var is_on: Int,
    var download_url: String
) : Parcelable