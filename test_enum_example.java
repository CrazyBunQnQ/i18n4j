package com.example.test;

/**
 * 测试用的Java枚举类
 * 用于验证enum_updater脚本的功能
 */
public enum TestDictionary {
    
    /**
     * 在线状态
     */
    ONLINE("在线", "common.status.online", 1),
    
    /**
     * 离线状态
     */
    OFFLINE("离线", "common.status.offline", 0),
    
    /**
     * 待处理状态
     */
    PENDING("待处理"),
    
    /**
     * 已完成状态
     */
    COMPLETED("已完成", "common.status.completed", 2, true),
    
    /**
     * 失败状态
     */
    FAILED("失败", "system.message.failure", -1, false),
    
    /**
     * 未知状态
     */
    UNKNOWN("未知", "common.unknown");
    
    private final String name;
    private final int code;
    private final boolean active;
    
    TestDictionary(String name) {
        this(name, 0, false);
    }
    
    TestDictionary(String name, int code) {
        this(name, code, false);
    }
    
    TestDictionary(String name, int code, boolean active) {
        this.name = name;
        this.code = code;
        this.active = active;
    }
    
    public String getName() {
        return name;
    }
    
    public int getCode() {
        return code;
    }
    
    public boolean isActive() {
        return active;
    }
}