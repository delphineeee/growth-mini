from __future__ import annotations


SKILL_PROJECTS = {
    "RAG/知识库": ("可评测的 RAG 问答助手", "一个包含小型文档集、检索、回答引用和10条评测集的可运行仓库"),
    "Agent 评测": ("Agent 自动化评测台", "一个能够批量运行任务、记录成功率与失败原因的评测脚本和报告"),
    "MCP/工具调用": ("带工具调用的任务 Agent", "一个至少接入两个安全工具、能展示调用轨迹和错误处理的 Agent"),
    "Agent 框架": ("最小 Agent 工作流", "一个具备状态、工具、失败重试和可观察日志的工作流 Demo"),
    "Memory/上下文工程": ("有记忆的对话 Agent", "一个能区分短期与长期信息、并能说明检索依据的 Demo"),
    "Multi-Agent": ("可审计的多 Agent 协作 Demo", "一个明确分工、传递结构化状态并能展示各步骤输出的工作流"),
    "Python": ("可测试的 Python 服务", "一个包含类型标注、异常处理、单元测试和清晰 README 的小型服务"),
    "推理服务与部署": ("可部署的模型调用服务", "一个包含健康检查、超时、重试、日志和部署说明的 API 服务"),
}


def generate_sprint(skill: str, daily_minutes: int) -> dict:
    title, deliverable = SKILL_PROJECTS.get(
        skill,
        (f"{skill} 证据项目", f"一个能够证明你实际使用过“{skill}”、包含测试与说明文档的小型作品"),
    )
    multipliers = [0.7, 0.9, 1.2, 1.2, 1.0, 1.0, 0.7]
    tasks = [
        ("定义问题与验收", "写清目标用户、输入输出、3条成功标准和3条失败案例。", "仓库中存在 scope.md；成功标准可由他人逐条检查。"),
        ("最小技术验证", f"只验证 {skill} 的一个核心机制，记录成功与失败。", "有可重复运行的最小脚本；README写明运行命令和观察结果。"),
        ("完成主链路", "把输入、核心处理和输出连通，不增加非核心页面。", "从示例输入到结果输出可以一次运行完成，无需手改中间文件。"),
        ("加入证据与错误处理", "保存关键中间结果、来源或调用轨迹，并处理至少两个常见错误。", "演示中能看见证据/轨迹；两个错误场景有明确提示且不会崩溃。"),
        ("建立小型评测", "准备10条测试样例，记录成功、失败及原因。", "evals目录含10条样例；脚本输出总成功率和失败清单。"),
        ("整理作品表达", "补充架构图、技术选择、局限性和截图；删除无法证明的宣传语。", "README能让陌生人在10分钟内运行；所有结论都有代码、测试或截图支持。"),
        ("结项与复盘", "运行全部测试，形成能力证据卡和一条不编造数据的简历描述草稿。", "测试通过；提供仓库链接、评测结果、实际耗时和下一步改进。"),
    ]
    days = []
    for index, (theme, task, acceptance) in enumerate(tasks, start=1):
        days.append({
            "day": index,
            "theme": theme,
            "task": task,
            "acceptance": acceptance,
            "estimated_minutes": max(30, round(daily_minutes * multipliers[index - 1] / 15) * 15),
        })
    return {
        "skill": skill,
        "title": title,
        "deliverable": deliverable,
        "days": days,
        "estimated_total_minutes": sum(day["estimated_minutes"] for day in days),
    }


def build_report(estimated_minutes: int, checkins: list[dict]) -> dict:
    completed = sum(1 for item in checkins if item.get("completed"))
    actual = sum(item.get("actual_minutes", 0) for item in checkins)
    artifacts = [item.get("artifact_url") for item in checkins if item.get("artifact_url")]
    completion_rate = round(completed / 7 * 100, 1)
    estimation_error = None
    if estimated_minutes:
        estimation_error = round((actual - estimated_minutes) / estimated_minutes * 100, 1)
    return {
        "completed_days": completed,
        "completion_rate": completion_rate,
        "estimated_minutes": estimated_minutes,
        "actual_minutes": actual,
        "estimation_error_percent": estimation_error,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "evidence_level": "verified" if completed >= 6 and artifacts else "claimed" if completed >= 3 else "none",
    }
