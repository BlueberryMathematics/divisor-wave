namespace DivisorWavePlotter;

sealed class LaunchOptions
{
    public long ParentHwnd { get; set; } = 0;
    public int  EmbedX     { get; set; } = 0;
    public int  EmbedY     { get; set; } = 30;
    public int  Width      { get; set; } = 960;
    public int  Height     { get; set; } = 680;
}
