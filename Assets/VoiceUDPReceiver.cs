using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class VoiceUDPReceiver : MonoBehaviour
{
    public int listenPort = 5005;
    private UdpClient udpClient;
    private Thread receiveThread;
    private bool running = false;

    private string latestCommand = null;
    private readonly object lockObj = new object();

    void Start()
    {
        udpClient = new UdpClient(listenPort);
        running = true;
        receiveThread = new Thread(ReceiveLoop);
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    void ReceiveLoop()
    {
        IPEndPoint remoteEP = new IPEndPoint(IPAddress.Any, listenPort);
        while (running)
        {
            try
            {
                byte[] data = udpClient.Receive(ref remoteEP);
                string msg = Encoding.UTF8.GetString(data);
                lock (lockObj)
                {
                    latestCommand = msg;
                }
                Debug.Log("받은 명령어: " + msg);
            }
            catch (SocketException) { }
        }
    }

    void Update()
    {
        string cmd = null;
        lock (lockObj)
        {
            if (latestCommand != null)
            {
                cmd = latestCommand;
                latestCommand = null;
            }
        }

        if (cmd != null)
        {
            HandleCommand(cmd);
        }
    }

    void HandleCommand(string cmd)
    {
        if (cmd == "HELLO")
        {
            Debug.Log("HELLO 명령어 → 캐릭터 인사 애니메이션");
            // animator.SetTrigger("Hello");
        }
        else if (cmd == "EAT")
        {
            Debug.Log("EAT 명령어 → 캐릭터 식사 애니메이션");
            // animator.SetTrigger("Eat");
        }
        else if (cmd == "CUTE")
        {
            Debug.Log("CUTE 명령어 → 캐릭터 부끄러움 애니메이션");
            // animator.SetTrigger("Cute");
        }
    }

    void OnApplicationQuit()
    {
        running = false;
        if (udpClient != null)
        {
            udpClient.Close();
        }
    }
}
