import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, FlatList, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing, Radius } from '../theme';
import { messaging } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function ConversationScreen({ route }) {
  const { correspondanceId } = route.params;
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const flatListRef = useRef(null);

  const load = async () => {
    try {
      const data = await messaging.conversation(correspondanceId);
      setMessages(data.messages || []);
    } catch { /* ignore */ }
  };

  useEffect(() => { load(); const interval = setInterval(load, 10000); return () => clearInterval(interval); }, []);

  const handleSend = async () => {
    const content = text.trim();
    if (!content || sending) return;
    setSending(true);
    try {
      const msg = await messaging.send(correspondanceId, content);
      setMessages(prev => [...prev, msg]);
      setText('');
      setTimeout(() => flatListRef.current?.scrollToEnd(), 100);
    } catch { /* ignore */ }
    setSending(false);
  };

  const formatTime = (d) => new Date(d).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

  const renderMessage = ({ item }) => {
    const isMe = item.sender_username === user?.username;
    return (
      <View style={[styles.msgRow, isMe && styles.msgRowMe]}>
        <View style={[styles.bubble, isMe ? styles.bubbleMe : styles.bubbleOther]}>
          {!isMe && <Text style={styles.senderName}>{item.sender_username}</Text>}
          <Text style={[styles.msgText, isMe && styles.msgTextMe]}>{item.content}</Text>
          <Text style={[styles.msgTime, isMe && styles.msgTimeMe]}>{formatTime(item.created_at)}</Text>
        </View>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined} keyboardVerticalOffset={90}>
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={item => String(item.id)}
        renderItem={renderMessage}
        contentContainerStyle={styles.list}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: false })}
      />

      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          placeholder="Écrire un message..."
          placeholderTextColor={Colors.textMuted}
          value={text}
          onChangeText={setText}
          multiline
          maxLength={1000}
        />
        <TouchableOpacity
          style={[styles.sendBtn, (!text.trim() || sending) && styles.sendBtnDisabled]}
          onPress={handleSend}
          disabled={!text.trim() || sending}
        >
          <Ionicons name="send" size={20} color={Colors.white} />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  list: { padding: Spacing.md, paddingBottom: Spacing.sm },
  msgRow: { marginBottom: Spacing.sm, alignItems: 'flex-start' },
  msgRowMe: { alignItems: 'flex-end' },
  bubble: { maxWidth: '78%', padding: Spacing.sm, borderRadius: Radius.lg },
  bubbleMe: { backgroundColor: Colors.earth, borderBottomRightRadius: 4 },
  bubbleOther: { backgroundColor: Colors.bgCard, borderBottomLeftRadius: 4, borderWidth: 1, borderColor: Colors.borderLight },
  senderName: { fontSize: 11, fontWeight: '600', color: Colors.earth, marginBottom: 2 },
  msgText: { fontSize: 14, color: Colors.text, lineHeight: 20 },
  msgTextMe: { color: Colors.white },
  msgTime: { fontSize: 10, color: Colors.textMuted, alignSelf: 'flex-end', marginTop: 4 },
  msgTimeMe: { color: Colors.white + 'AA' },
  inputBar: {
    flexDirection: 'row', alignItems: 'flex-end', padding: Spacing.sm,
    backgroundColor: Colors.bgCard, borderTopWidth: 1, borderTopColor: Colors.borderLight,
  },
  input: {
    flex: 1, backgroundColor: Colors.bg, borderRadius: Radius.lg, paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm, fontSize: 14, maxHeight: 100, color: Colors.text,
  },
  sendBtn: {
    width: 40, height: 40, borderRadius: 20, backgroundColor: Colors.earth,
    alignItems: 'center', justifyContent: 'center', marginLeft: Spacing.sm,
  },
  sendBtnDisabled: { opacity: 0.4 },
});
