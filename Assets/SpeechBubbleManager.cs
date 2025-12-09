using UnityEngine;
using TMPro;

public class SpeechBubbleManager : MonoBehaviour
{
    public GameObject qaBubblePrefab;
    public Transform bubbleParent;

    public void ShowQA(string question, string sentiment, string[] keywords, string answer, string persona)
    {
        if (qaBubblePrefab == null || bubbleParent == null)
        {
            Debug.LogWarning("SpeechBubbleManager 설정이 안 됨");
            return;
        }

        GameObject bubble = Instantiate(qaBubblePrefab, bubbleParent);

        string keywordText = (keywords != null && keywords.Length > 0)
            ? string.Join(", ", keywords)
            : "키워드 없음";

        string personaText = string.IsNullOrEmpty(persona) ? "기본" : persona;

        var texts = bubble.GetComponentsInChildren<TextMeshProUGUI>();
        foreach (var t in texts)
        {
            if (t.name.Contains("Question"))
                t.text = $"Q: {question}";
            else if (t.name.Contains("Sentiment"))
                t.text = $"감정: {sentiment}";
            else if (t.name.Contains("Keywords"))
                t.text = $"키워드: {keywordText}";
            else if (t.name.Contains("Answer"))
                t.text = $"A: {answer}";
            else if (t.name.Contains("Persona"))
                t.text = $"성격: {personaText}";
        }

        Destroy(bubble, 7f); // 7초 후 자동 삭제
    }
}
